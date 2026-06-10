# flx: Fixed-length fingerprint representation extractor

It contains an implementation of [DeepPrint](https://arxiv.org/abs/1909.09901), a Deep Learning based fixed-length Fingerprint Representation extractor. The fine-tuned model checkpoints used for this system can be provided upon request.

Using the `flx` package
------------

### Installation

To install the package, clone the repository and run `pip install -e .` in the root directory of the repository.

The package requires Python 3.9 or higher. Other dependencies are listed in the `requirements.txt` file. Install them with

```pip install -r requirements.txt```

### Usage

You can import modules from the `flx` package in your own scripts and use them to train models, generate embeddings and run benchmarks.


### Pre-trained model

The model for an embedding size of 512 can be found under the link
[Google Drive](https://drive.google.com/drive/folders/1vV2skXApZMhqWTlF2j_qgXDxRYan5U1f?usp=drive_link)

Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment
    ├── setup.py           <- makes project pip installable (pip install -e .) so you can  `import flx. ...`
    ├── figures            <- Figures for the README
    ├── models             <- Trained and serialized models, training logs
    ├── notebooks          <- Jupyter notebooks for tutorials and examples
    ├── tests              <- Some unit tests for the package. Run with `pytest`.
    │
    ├── data
    │   ├── benchmarks     <- Folder for the benchmark specifications (i.e. which comparisons to run)
    │   ├── poses          <- Folder for poses of a corresponding fingerprint dataset.
    │   ├── embeddings     <- Output folder for fingerprint embeddings.
    │   └── fingerprints   <- Folder with fingerprint datasets.
    │
    ├── reports            <- Contains folders with the full benchmark results of all trained models
    │   ├── ...            <- Output folders for the benchmark results (in .json format) are here.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    └── flx                <- Source code for use in this project.
        │
        ├── benchmarks     <- Implementation of biometric performance benchmarks (verification, identification)
        ├── data           <- Code to manage datasets of fingerprints, poses, embeddings etc.
        ├── extractor      <- Embedding extraction code using the DeepPrint model
        ├── models         <- DeepPrint model architectures, loss functions and pytorch code for training
        ├── preprocessing  <- Data augmentation and contrast enhancement
        ├── reweighting    <- Code to reweight embedding dimensions after extraction
        ├── scripts        <- Different scripts for running benchmarks, generating embeddings etc.
        ├── setup          <- Settings, predefined models and datasets are defined here. This allows to easily benchmark different models and datasets.
        └── visualization  <- Contains functions for visualization and graphical debugging
     
--------

### Credit to other authors:

- Remi Cadene; Inception v4 pytorch implementation (see `flx/models/Inceptionv4.py`); https://github.com/Cadene/pretrained-models.pytorch

- Dong Chengdong Hang Zhou; iso-19794-2 fingerprint template encoder and decoder (see `flx/data/iso-encoder-decoder`); https://github.com/DongChengdongHangZhou/iso-19794-2-decoder-encoder


Paper: Benchmarking fixed-length Fingerprint Representations across different Embedding Sizes and Sensor Types
------------

### Abstract

Traditional minutiae-based fingerprint representations consist of a variable-length set of
minutiae. This necessitates a more complex comparison causing the drawback of high computational cost in one-to-many comparison. Recently, deep neural networks have been proposed to extract fixed-length embeddings from fingerprints. In this paper, we explore to what extent fingerprint
texture information contained in such embeddings can be reduced in terms of dimension, while preserving high biometric performance. This is of particular interest, since it would allow to reduce
the number of operations incurred at comparisons. We also study the impact in terms of recognition
performance of the fingerprint textural information for two sensor types, i.e. optical and capacitive.
Furthermore, the impact of rotation and translation of fingerprint images on the extraction of fingerprint embeddings is analysed. Experimental results conducted on a publicly available database reveal an optimal embedding size of 512 feature elements for the texture-based embedding part of fixed-length fingerprint representations. In addition, differences in performance between sensor types can be perceived.



### Deep Print

The full DeepPrint model consists of the following components:
 - Localization network: Localizes the fingerprint in the image and crops it to a fixed size. (Not shown in the figure)
 - Inception v4 stem: Processes the fingerprint image and extracts a feature map.
 - Texture-branch: Processes the feature map and extracts a fixed-length fingerprint representation.
 - Minutiae-branch: Processes the feature map and extracts a fixed-length minutiae representation as well as a minutia map. The minutia map is used during training to focus the training on the minutiae regions of the fingerprint. It is not used to create the fixed-length fingerprint representation.

In this project, many smaller variants of the DeepPrint model were examined. In the code, the naming convention is:

`DeepPrint_[Loc][Tex][Minu]_<NDIMS>`

Where `[Loc]` means that the localization network is included, `[Tex]` means that the texture branch is included and `[Minu]` means that the minutiae branch is included. `<NDIMS>` is the dimensionality of the fixed-length fingerprint representation (i.e. the number of neurons in the last linear layer).

### Matching Logic & Embedding Size

The model extracts a **512-dimensional fixed-length embedding** from each fingerprint image. This combines 256 dimensions from the texture branch and 256 dimensions from the minutiae branch into a single vector. 

During the verification phase, these 512-dimensional vectors are compared against stored enrolled embeddings using **cosine similarity**. A live scan is compared against all saved templates for a user. If the similarity score meets or exceeds the required threshold (e.g., ≥ 0.75) for a majority of the stored samples (e.g., at least 4 out of 6 matches), the authentication is considered successful.

### Databases

In the code we do not distinguish between different fingers of one subject and different fingers from separate subjects. Instead, we use the term "subject" to refer a distinct fingerprint. The term "impression" refers to a single sample / capture of a fingerprint. This deviates a bit from the terminology used in the paper. In these terms, the databases used in the paper are:

In the paper, a synthetic databases created with the `SFinge` synthetic fingerprint generator were used for training (6000 subjects à 10 impressions) and validation (2000 subjects à 4 impressions).

In addition MCYT330 optical and capacitive sensor databases (3300 subjects à 2 sensors à 12 impressions) were used. The first 2000 subjects were used for training and the remaining 1300 subjects were used for testing.

There is also code to load and benchmark for FVC2004 DB1 and SD4 databases. However, these were not used in the paper.

### Image processing

The input size of DeepPrint is 299x299 pixels. How the resizing and cropping is done depends on the source dataset and can be found in the `flx/data/image-loader.py` file.

During training, data augumentation is applied to the fingerprint images. The following augmentations are applied:

 - Random rotation between -15° and 15°
 - Random translation of up to 25 pixels in x and y direction
 - Random gain and contrast adjustment (see `flx/setup/datasets.py` -> `QUALITY_AUGMENTATION`)
