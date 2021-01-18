import conducto as co

import numpy as np
import pandas as pd
import scanpy as sc


co.nb.matplotlib_inline()


def preprocess(in_path, out_path=None):
    # Read data
    with co.nb.cell():
        # ### Load data
        adata = sc.read_10x_mtx(
            in_path,  # the directory with the `.mtx` file
            var_names='gene_symbols',  # use gene symbols for the variable names (variables-axis index)
            cache=True)  # write a cache file for faster subsequent reading
        adata.var_names_make_unique()  # this is unnecessary if using `var_names='gene_ids'` in `sc.read_10x_mtx`

    with co.nb.cell():
        # Show those genes that yield the highest fraction of counts in each single cell, across all cells.
        sc.pl.highest_expr_genes(adata, n_top=20)

    with co.nb.cell():
        # Basic filtering
        sc.pp.filter_cells(adata, min_genes=200)
        sc.pp.filter_genes(adata, min_cells=3)

    with co.nb.cell():
        # With pp.calculate_qc_metrics, we can compute many metrics very efficiently.
        adata.var['mt'] = adata.var_names.str.startswith('MT-')  # annotate the group of mitochondrial genes as 'mt'
        sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)

    with co.nb.cell():
        # A violin plot of some of the computed quality measures:
        # * the number of genes expressed in the count matrix
        # * the total counts per cell
        # * the percentage of counts in mitochondrial genes
        sc.pl.violin(adata, ['n_genes_by_counts', 'total_counts', 'pct_counts_mt'],
                     jitter=0.4, multi_panel=True)

    with co.nb.cell():
        # Remove cells that have too many mitochondrial genes expressed or too many total counts:
        sc.pl.scatter(adata, x='total_counts', y='pct_counts_mt')
        sc.pl.scatter(adata, x='total_counts', y='n_genes_by_counts')

    with co.nb.cell():
        # Actually do the filtering by slicing the `AnnData` object.
        adata = adata[adata.obs.n_genes_by_counts < 2500, :]
        adata = adata[adata.obs.pct_counts_mt < 5, :]

    with co.nb.cell():
        # Total-count normalize (library-size correct) the data matrix 𝐗
        # to 10,000 reads per cell, so that counts become comparable among cells.
        sc.pp.normalize_total(adata, target_sum=1e4)

    with co.nb.cell():
        # Logarithmize the data:
        sc.pp.log1p(adata)

    with co.nb.cell():
        # Identify highly-variable genes.
        sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
        sc.pl.highly_variable_genes(adata)

    with co.nb.cell():
        # Set the `.raw` attribute of the AnnData object to the normalized and logarithmized raw gene expression for later use in differential testing and visualizations of gene expression. This simply freezes the state of the AnnData object.
        #
        # Note: You can get back an `AnnData` of the object in `.raw` by calling `.raw.to_adata()`.
        adata.raw = adata

    with co.nb.cell():
        # If you don’t proceed below with correcting the data with `sc.pp.regress_out` and scaling it via `sc.pp.scale`, you can also get away without using `.raw` at all.
        #
        # The result of the previous highly-variable-genes detection is stored as an annotation in `.var.highly_variable` and auto-detected by PCA and hence, `sc.pp.neighbors` and subsequent manifold/graph tools. In that case, the step actually do the filtering below is unnecessary, too.

        # Actually do the filtering
        adata = adata[:, adata.var.highly_variable]

        # Regress out effects of total counts per cell and the percentage of mitochondrial genes expressed. Scale the data to unit variance.
        sc.pp.regress_out(adata, ['total_counts', 'pct_counts_mt'])

        # Scale each gene to unit variance. Clip values exceeding standard deviation 10.
        sc.pp.scale(adata, max_value=10)

    # Save data
    if out_path is not None:
        adata.write(out_path)


def pca(in_path, out_path=None):
    adata = sc.read(in_path)

    with co.nb.cell():
        # Reduce the dimensionality of the data by running principal component analysis (PCA), which reveals the main axes of variation and denoises the data.
        sc.tl.pca(adata, svd_solver='arpack')

    with co.nb.cell():
        # We can make a scatter plot in the PCA coordinates, but we will not use that later on.
        sc.pl.pca(adata, color='CST3')

    with co.nb.cell():
        # Let us inspect the contribution of single PCs to the total variance in the data. This gives us information about how many PCs we should consider in order to compute the neighborhood relations of cells, e.g. used in the clustering function `sc.tl.louvain()` or tSNE `sc.tl.tsne()`. In our experience, often a rough estimate of the number of PCs does fine.
        sc.pl.pca_variance_ratio(adata, log=True)

    print(adata)

    # Save the result.
    if out_path is not None:
        adata.write(out_path)


def neighborhood(in_path, out_path=None):
    adata = sc.read(in_path)

    with co.nb.cell():
        # ### Computing the neighborhood graph
        #
        # Let us compute the neighborhood graph of cells using the PCA representation of the data matrix. You might simply use default values here. For the sake of reproducing Seurat’s results, let’s take the following values.
        sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)

    with co.nb.cell():
        # ### Embedding the neighborhood graph
        #
        # We suggest embedding the graph in two dimensions using UMAP (McInnes et al., 2018), see below. It is potentially more faithful to the global connectivity of the manifold than tSNE, i.e., it better preserves trajectories. In some ocassions, you might still observe disconnected clusters and similar connectivity violations. They can usually be remedied by running:
        #
        # ```
        # tl.paga(adata)
        # pl.paga(adata, plot=False)  # remove `plot=False` if you want to see the coarse-grained graph
        # tl.umap(adata, init_pos='paga')
        # ```
        sc.tl.umap(adata)
        sc.pl.umap(adata, color=['CST3', 'NKG7', 'PPBP'])

    with co.nb.cell():
        # As we set the `.raw` attribute of `adata`, the previous plots showed the “raw” (normalized, logarithmized, but uncorrected) gene expression. You can also plot the scaled and corrected gene expression by explicitly stating that you don’t want to use `.raw`.
        sc.pl.umap(adata, color=['CST3', 'NKG7', 'PPBP'], use_raw=False)

    with co.nb.cell():
        # ### Clustering the neighborhood graph
        #
        # As with Seurat and many other frameworks, we recommend the Leiden graph-clustering method (community detection based on optimizing modularity) by [Traag *et al.* (2018)](https://scanpy.readthedocs.io/en/latest/references.html#traag18). Note that Leiden clustering directly clusters the neighborhood graph of cells, which we already computed in the previous section.
        sc.tl.leiden(adata)

    with co.nb.cell():
        # Plot the clusters, which agree quite well with the result of Seurat.
        sc.pl.umap(adata, color=['leiden', 'CST3', 'NKG7'])

    # Save the result.
    if out_path is not None:
        adata.write(out_path)


def marker(method, in_path, out_path=None):
    adata = sc.read(in_path)

    if method == "t-test":
        with co.nb.cell():
            # ### Finding marker genes
            #
            # Let us compute a ranking for the highly differential genes in each cluster. For this, by default, the .raw attribute of AnnData is used in case it has been initialized before. The simplest and fastest method to do so is the t-test.
            sc.tl.rank_genes_groups(adata, 'leiden', method='t-test')
            sc.pl.rank_genes_groups(adata, n_genes=25, sharey=False)

    elif method == "wilcoxon":
        sc.settings.verbosity = 2  # reduce the verbosity

        with co.nb.cell():
            # The result of a [Wilcoxon rank-sum (Mann-Whitney-U)](https://de.wikipedia.org/wiki/Wilcoxon-Mann-Whitney-Test) test is very similar. We recommend using the latter in publications, see e.g., [Sonison & Robinson (2018)](https://doi.org/10.1038/nmeth.4612). You might also consider much more powerful differential testing packages like MAST, limma, DESeq2 and, for python, the recent diffxpy.
            sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')
            sc.pl.rank_genes_groups(adata, n_genes=25, sharey=False)
    elif method == "logreg":
        with co.nb.cell():
            # As an alternative, let us rank genes using logistic regression. For instance, this has been suggested by [Natranos et al. (2018)](https://doi.org/10.1101/258566). The essential difference is that here, we use a multi-variate appraoch whereas conventional differential tests are uni-variate. [Clark et al. (2014)](https://doi.org/10.1186/1471-2105-15-79) has more details.
            sc.tl.rank_genes_groups(adata, 'leiden', method='logreg')
            sc.pl.rank_genes_groups(adata, n_genes=25, sharey=False)
    else:
        raise ValueError(f"Unknown analysis method: {method}. Expected 't-test', 'wilcoxon', or 'logreg'.")

    with co.nb.cell():
        # Let us also define a list of marker genes for later reference.
        marker_genes = ['IL7R', 'CD79A', 'MS4A1', 'CD8A', 'CD8B', 'LYZ', 'CD14',
                        'LGALS3', 'S100A8', 'GNLY', 'NKG7', 'KLRB1',
                        'FCGR3A', 'MS4A7', 'FCER1A', 'CST3', 'PPBP']

    with co.nb.cell():
        # With the exceptions of IL7R, which is only found by the t-test and FCER1A, which is only found by the other two approaches, all marker genes are recovered in all approaches.
        # | Louvain Group |	Markers	| Cell Type |
        # | ------------- | ------- | --------- |
        # | 0 |	IL7R |	CD4 T cells |
        # | 1 |	CD14, LYZ |	CD14+ Monocytes |
        # | 2 |	MS4A1 |	B cells |
        # | 3 |	CD8A |	CD8 T cells |
        # | 4 |	GNLY, NKG7 |	NK cells |
        # | 5 |	FCGR3A, MS4A7 |	FCGR3A+ Monocytes |
        # | 6 |	FCER1A, CST3 |	Dendritic Cells |
        # | 7 |	PPBP |	Megakaryocytes |
        pass

    with co.nb.cell():
        # Show the 10 top ranked genes per cluster 0, 1, …, 7 in a dataframe.
        df = pd.DataFrame(adata.uns['rank_genes_groups']['names']).head(5)
        print(df.to_markdown())

    with co.nb.cell():
        # Get a table with the scores and groups.
        result = adata.uns['rank_genes_groups']
        groups = result['names'].dtype.names
        df = pd.DataFrame(
            {group + '_' + key[:1]: result[key][group]
             for group in groups for key in ['names', 'pvals']}).head(5)
        print(df.to_markdown())

    with co.nb.cell():
        # Compare to a single cluster:
        sc.tl.rank_genes_groups(adata, 'leiden', groups=['0'], reference='1', method='wilcoxon')
        sc.pl.rank_genes_groups(adata, groups=['0'], n_genes=20)

    with co.nb.cell():
        # If we want a more detailed view for a certain group, use `sc.pl.rank_genes_groups_violin`.
        sc.pl.rank_genes_groups_violin(adata, groups='0', n_genes=8)

    with co.nb.cell():
        # If you want to compare a certain gene across groups, use the following.
        sc.pl.violin(adata, ['CST3', 'NKG7', 'PPBP'], groupby='leiden')

    with co.nb.cell():
        # Actually mark the cell types.
        new_cluster_names = [
            'CD4 T', 'CD14 Monocytes',
            'B', 'CD8 T',
            'NK', 'FCGR3A Monocytes',
            'Dendritic', 'Megakaryocytes']
        adata.rename_categories('leiden', new_cluster_names)
        sc.pl.umap(adata, color='leiden', legend_loc='on data', title='', frameon=False, save='.pdf')

    with co.nb.cell():
        # Now that we annotated the cell types, let us visualize the marker genes.
        sc.pl.dotplot(adata, marker_genes, groupby='leiden')

    with co.nb.cell():
        # There is also a very compact violin plot.
        sc.pl.stacked_violin(adata, marker_genes, groupby='leiden', rotation=90)

    print(adata)

    # Save the result.
    adata.write(out_path)

if __name__ == "__main__":
    co.main()