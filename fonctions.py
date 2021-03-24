# %% Import

from files import *
from database import *
from statistics import mean
from sklearn.linear_model import LinearRegression
import random as r
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3

# %% Connecteur SQLite3
con = sqlite3.connect('resultats.db')

# %% Fonctions de création de dictionnaires d'arrivées

def cree_arrivee(d, f, loi_nbr_clients, loi_poids):
    """
    Genere des arrivees de clients suivant des lois données.
    loi_nbr_clients : lambda, n -> Renvoie une liste de n nombres de clients (moyenne lambda)
    loi_poids : lambda -> Renvoie un poids (moyenne lambda)
    """
    arr_par_inst = loi_nbr_clients(f-d)
    A = dict()
    for i in range(f-d):
        if arr_par_inst[i] != 0:
            A[i+d] = []
            for j in range(arr_par_inst[i]):
                A[i+d].append(Client(poids=loi_poids()))
    return A

def poisson(n, lam, poids_moy):
    """Genere des arrivees de λ clients par unite de temps en moyenne, suivant une loi de poisson."""
    loi_arr = lambda n: np.random.poisson(lam, n)
    loi_p = lambda: np.random.poisson(poids_moy)
    return cree_arrivee(0, n, loi_arr, loi_p)

def echelon(d, f, p, n):
    """Crée un échellon, d : début, f : fin, p : poids, n : nombre de clients"""
    loi_arr = lambda i: [n for _ in range(i)]
    loi_p = lambda: p
    return cree_arrivee(d, f, loi_arr, loi_p)

def fusionne_arrivees(A, B):
    """Renvoie l'arrivée formée des deux dictionnaires d'arrivés fusionnés"""
    C = deepcopy(A)
    for b in B:
        if b in A:
            for client in B[b]:
                C[b].append(client)
        else:
            C[b] = B[b]
    return C

def fusionne_liste(liste):
    """Fusionne une liste de dictionnaire d'arrivées récursivement"""
    if len(liste) == 1:
        return liste[0]
    else:
        return fusionne_arrivees(liste.pop(0), fusionne_liste(liste))

# %% Différents serveurs

# Poids moyen enlevé par unité de temps
λ = 10
# n = 5
# np.random.binomial(n, λ/n, 10)
FIFO_d = Serveur_FIFO(lambda:λ, λ, 'FIFO_d')
FIFO_p = Serveur_FIFO(lambda: np.random.poisson(λ), λ, 'FIFO_p')
# FIFO_b = Serveur_FIFO(lambda: np.random.binomial(n, λ/n), λ, FIFO_b)
LIFO_d = Serveur_LIFO(lambda:λ, λ, 'LIFO_d')
RR_d = Serveur_RR(lambda:λ, λ//10, λ, 'RR_d')
RR_p = Serveur_RR(lambda: np.random.poisson(λ), λ//10, λ, 'RR_p')
PRIO_d = Serveur_Prio(lambda:λ, λ, 'PRIO_d')
PRIO_p = Serveur_Prio(lambda: np.random.poisson(λ), λ, 'PRIO_p')

# %% Différentes files d'exemple

F1 = File(K=200, serveurs=[FIFO_p], couleur='red')
F2 = File(K=200, serveurs=[PRIO_p], couleur='blue')

# %% Différentes arrivées
n = 10**4
A1 = poisson(n, 10, 1)
A2 = poisson(n, 5, 2)
A3 = poisson(n, 2, 5)
A4 = poisson(n, 1, 10)
A5 = echelon(100, 110, 2, 3)

# %%%% Affichages de différents Résultats
# %% Remplissage du buffer en fonction du temps
def plot_taille_buffer(F_liste, A):
    # Plot
    fig, axs = plt.subplots(2)
    ax1, ax2 = axs
    fig.set_size_inches(10, 5)
    ax2.grid(True)
    # fig.tight_layout()

    for F in F_liste:
        tailles = []
        pertes = []
        nom = str(F.serveurs[0])[:4]

        F.reset()
        F.A = deepcopy(A)

        start = time.time()
        while not F.file_vide():
            tailles.append(F.nbr_clients())
            pertes.append(F.pertes)
            F.iteration()

        # print("Simulation finie en : {} secondes".format(time.time()-start))

        T = [i for i in range(len(tailles))]
        # ax1.hlines(F.K, 0, n, color='grey', alpha = .5)

        # plt.subplot(211)
        ax1.plot(tailles, label='Buffer {}'.format(nom), color=F.couleur)
        ax1.set_title('Nombre de clients dans le buffer')
        ax1.legend(loc=2)
        ax1.set_xlabel('t')

        # plt.subplot(212)
        ax2.plot(pertes, label='Pertes {}'.format(nom), color=F.couleur)
        ax2.set_title('Pertes')
        ax2.legend(loc=2)
        ax2.set_xlabel('t')

plot_taille_buffer([F1, F2], A1)
plot_taille_buffer([F1, F2], A4)

# %% Little
def verifie_Little():
    query ='SELECT attente_moyen as Attente_moyenne, nbr_clients_moyen*poids_moyen/10 as Nombre_sortie_normalisé FROM Simulation\
            JOIN Files ON Files.id = file_id\
            JOIN Arrivees ON Arrivees.id = id_arrivee'
    little_df = pd.read_sql(sql=query, con=con)
    little_df.plot.scatter(x=0, y=1, color='blue', figsize=(10,6), s=5)
    # little_df.plot(x=0, y=1)
    x=little_df['Attente_moyenne'].to_numpy()
    y=little_df['Nombre_sortie_normalisé'].to_numpy()

verifie_Little()

# %%
