import csv
import os
import shutil
import subprocess
import sys

from Bio import SeqIO
from shutil import which

from esmecata.utils import is_valid_path, is_valid_dir

def make_clustering(proteome_folder, output_folder, nb_cpu, clust_threshold):
    if not which('mmseqs'):
        print('mmseqs not available in path, esmecata will not be able to cluster the proteomes.')
        sys.exit(1)

    if not is_valid_dir(proteome_folder):
        print(f"Input must be a folder {proteome_folder}.")
        sys.exit(1)

    # Use the result folder created by retrieve_proteome.py.
    result_folder = os.path.join(proteome_folder, 'result')
    if not is_valid_path(result_folder):
        print(f"Missing output from esmecata proteomes in {result_folder}.")
        sys.exit(1)

    is_valid_dir(output_folder)

    cluster_fasta_files = {}
    for cluster in os.listdir(result_folder):
        result_cluster_folder = os.path.join(result_folder, cluster)
        if is_valid_dir(result_cluster_folder):
            for cluster_file in os.listdir(result_cluster_folder):
                filename, file_extension = os.path.splitext(cluster_file)
                if file_extension == '.faa':
                    cluster_file_path = os.path.join(result_cluster_folder, cluster_file)
                    if cluster not in cluster_fasta_files:
                        cluster_fasta_files[cluster] = [cluster_file_path]
                    else:
                        cluster_fasta_files[cluster].append(cluster_file_path)

    # Create tmp folder for mmseqs analysis.
    mmseqs_tmp = os.path.join(output_folder, 'mmseqs_tmp')
    is_valid_dir(mmseqs_tmp)

    # Create output folder containing shared representative proteins.
    reference_proteins_fasta = os.path.join(output_folder, 'reference_proteins_fasta')
    is_valid_dir(reference_proteins_fasta)

    print('Clustering proteins.')
    # For each OTU run mmseqs easy-cluster on them to found the clusters that have a protein in each proteome of the OTU.
    # We take the representative protein of a cluster if the cluster contains a protein from all the proteomes of the OTU.
    # If this condition is not satisfied the cluster will be ignored.
    # Then a fasta file containing all the representative proteins for each OTU is written in reference_proteins_fasta folder.
    for cluster in cluster_fasta_files:
        mmseqs_tmp_cluster = os.path.join(mmseqs_tmp, cluster)
        mmseqs_tmp_cluster_output = os.path.join(mmseqs_tmp_cluster, 'cluster')
        is_valid_dir(mmseqs_tmp_cluster)

        mmseqs_tmp_clustered_tabulated = mmseqs_tmp_cluster_output+'_cluster.tsv'
        mmseqs_tmp_representative_fasta = mmseqs_tmp_cluster_output + '_rep_seq.fasta'
        # Run mmmseqs to find rapidly protein clusters.

        """
        # Code using mmseqs database and mmseqs modules to cluster instead of easy-cluster.
        mmseqs_tmp_db = os.path.join(mmseqs_tmp_cluster, 'db')
        mmseqs_tmp_db_clustered = os.path.join(mmseqs_tmp_cluster, 'cluster_db')
        mmseqs_tmp_cluster_tmp = os.path.join(mmseqs_tmp_cluster, 'cluster_tmp')
        mmseqs_tmp_rep_cluster = os.path.join(mmseqs_tmp_cluster, 'cluster_rep')

        # Create database containing the protein sequences from all the proteomes of a taxon.
        subprocess.call(['mmseqs', 'createdb', *cluster_fasta_files[cluster], mmseqs_tmp_db, '-v', '2'])
        # Cluster the protein sequences.
        subprocess.call(['mmseqs', 'cluster', mmseqs_tmp_db, mmseqs_tmp_db_clustered, mmseqs_tmp_cluster_tmp, '--threads', str(nb_cpu), '-v', '2'])
        # Create TSV resulting files to be analysed after.
        subprocess.call(['mmseqs', 'createtsv', mmseqs_tmp_db, mmseqs_tmp_db, mmseqs_tmp_db_clustered, mmseqs_tmp_clustered_tabulated, '--threads', str(nb_cpu), '-v', '2'])
        # Create fasta fiel containing representative proteins (representatives are the first protein of the alignement).
        subprocess.call(['mmseqs', 'createsubdb', mmseqs_tmp_db_clustered, mmseqs_tmp_db, mmseqs_tmp_rep_cluster, '-v', '2'])
        subprocess.call(['mmseqs', 'convert2fasta', mmseqs_tmp_rep_cluster, mmseqs_tmp_representative_fasta, '-v', '2'])
        """

        # Code using easy-cluster to extract representative protein.
        subprocess.call(['mmseqs', 'easy-cluster', *cluster_fasta_files[cluster], mmseqs_tmp_cluster_output, mmseqs_tmp_cluster, '--threads', str(nb_cpu), '-v', '2'])

        # Extract protein clusters.
        proteins_representatives = {}
        with open(mmseqs_tmp_clustered_tabulated) as input_file:
            csvreader = csv.reader(input_file, delimiter='\t')
            for row in csvreader:
                if row[0] not in proteins_representatives:
                    proteins_representatives[row[0]] = [row[1]]
                else:
                    proteins_representatives[row[0]].append(row[1])

        # Retrieve protein ID and the corresponding proteome.
        organism_prots = {}
        for fasta_file in cluster_fasta_files[cluster]:
            filename, file_extension = os.path.splitext(fasta_file)
            for record in SeqIO.parse(fasta_file, 'fasta'):
                organism_prots[record.id.split('|')[1]] = fasta_file

        reference_proteins = os.path.join(output_folder, 'reference_proteins')
        is_valid_dir(reference_proteins)

        # To keep a cluster, we have to find have at least one protein of each proteome of the OTU.
        rep_prot_to_keeps = []
        rep_prot_organims = {}
        cluster_proteomes_output_file = os.path.join(reference_proteins, cluster+'.tsv')
        with open(cluster_proteomes_output_file, 'w') as output_file:
            csvwriter = csv.writer(output_file, delimiter='\t')
            for rep_protein in proteins_representatives:
                rep_prot_organims[rep_protein] = set([organism_prots[prot] for prot in proteins_representatives[rep_protein]])
                if len(rep_prot_organims[rep_protein]) >= clust_threshold * len(cluster_fasta_files[cluster]):
                    csvwriter.writerow([rep_protein, *[prot for prot in proteins_representatives[rep_protein]]])
                    rep_prot_to_keeps.append(rep_protein)

        # Create BioPtyhon records with the representative proteins kept.
        new_records = []
        for record in SeqIO.parse(mmseqs_tmp_representative_fasta, 'fasta'):
            if record.id.split('|')[1] in rep_prot_to_keeps:
                new_records.append(record)

        # Create output proteome file for OTU.
        reference_proteins_fasta_file = os.path.join(reference_proteins_fasta, cluster+'.faa')
        SeqIO.write(new_records, reference_proteins_fasta_file, 'fasta')

    proteome_taxon_id_file = os.path.join(proteome_folder, 'proteome_cluster_tax_id.tsv')
    clustering_taxon_id_file = os.path.join(output_folder, 'proteome_cluster_tax_id.tsv')

    if os.path.exists(clustering_taxon_id_file):
        if not os.path.samefile(proteome_taxon_id_file, clustering_taxon_id_file):
            os.remove(clustering_taxon_id_file)
            shutil.copyfile(proteome_taxon_id_file, clustering_taxon_id_file)
    else:
        shutil.copyfile(proteome_taxon_id_file, clustering_taxon_id_file)