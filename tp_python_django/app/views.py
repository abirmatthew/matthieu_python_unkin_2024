from django.shortcuts import render

# Create your views here.
import pandas as pd
import wfdb
import numpy as np

from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
# Charger les métadonnées
metadata = pd.read_csv('data/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3/ptbxl_database.csv')
base_path = 'data/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3/'  # Remplacez par le chemin réel des fichiers ECG

def index(request):
    """Affiche la page d'analyse ECG.""" 
    return render(request, 'index.html')

@api_view(['GET'])
def stream_data(request):
    """API pour diffuser les données ECG en temps réel."""
    record_id = int(request.GET.get('record_id', 1))  # ID de l'ECG à diffuser
    start = int(request.GET.get('start', 0))          # Position de début
    length = 500                                       # Nombre de points à envoyer (1 sec si 500 Hz)

    try:
        record_path = base_path + metadata.loc[record_id - 1, 'filename_hr']
        # Valider l'existence du fichier
        if not os.path.isfile(record_path + '.hea') or not os.path.isfile(record_path + '.dat'):
            return Response({'error': 'File not found'}, status=404)

        # Charger le fichier ECG
        record = wfdb.rdsamp(record_path)
        signal = record[0][:, 0]  # Première dérivation (lead 1)

        # Extraire un segment de données
        segment = signal[start:start + length]
        if len(segment) == 0:
            return Response({'data': [], 'end': True})

        return Response({
            'data': segment.tolist(),
            'start': start,
            'end': False,
            'metadata': {
                'age': metadata.loc[record_id - 1, 'age'],
                'sex': 'Male' if metadata.loc[record_id - 1, 'sex'] == 1 else 'Female',
                'scp_codes': metadata.loc[record_id - 1, 'scp_codes']
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import numpy as np

@api_view(['POST'])
def analyze_data(request):
    """
    Analyse des données envoyées depuis le frontend.
    Exemple : Détection simplifiée des pics R dans un signal ECG.
    """
    try:
        # Vérification des données reçues
        json_data = request.data
        if 'signal' not in json_data:
            return Response({'error': "Le champ 'signal' est manquant dans les données."}, status=status.HTTP_400_BAD_REQUEST)

        # Conversion du signal en tableau numpy
        signal = np.array(json_data['signal'], dtype=float)
        if signal.size == 0:
            return Response({'error': "Le tableau 'signal' est vide."}, status=status.HTTP_400_BAD_REQUEST)

        # Détection simplifiée des pics R
        mean_signal = np.mean(signal)
        r_peaks = np.where(signal > mean_signal)[0].tolist()

        return Response({'r_peaks': r_peaks}, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({'error': f"Erreur lors de la conversion du signal : {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f"Erreur inattendue : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

