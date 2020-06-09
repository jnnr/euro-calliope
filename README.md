# Euro Calliope

A model of the European power system built using Calliope.

This repository contains the routines that automatically generate the model from source data.

## Get ready

1. You need [conda](https://conda.io/docs/index.html) to build and use the model. Using conda, you can create a conda environment from within you can run it:

```
conda env create -f requirements.yml
conda activate euro-calliope
```

2. You need a Gurobi license installed on your computer, or you need to choose a different solver.

3. You need an account at the Copernicus Climate Data Service and you need to create a `$HOME/.cdsapirc` file with your credentials, see their [How To](https://cds.climate.copernicus.eu/api-how-to) (you do not need to manually install the client).

4. Further, you need all data files that cannot be retrieved automatically:

* [Maritime Boundaries v10 -> World Exclusive Economic Zones v10](http://www.marineregions.org/downloads.php), to be placed in `./data/World_EEZ_v10_20180221`
* [hydroBASINS -> Standard -> Europe and Middle East -> hybas_eu_lev07_v1c](https://www.hydrosheds.org/downloads) downloaded to `./data/hybas_eu_lev07_v1c/`
* spatio-temporal capacity factors in `./data/capacityfactors/`, where time and space dimensions are defined by two files:
    * an id map, where each pixel points to a time series: `./data/capacityfactors/{technology}-ids.tif`
    * all indexed time series: `./data/capacityfactors/{technology}-timeseries.nc`

## Generate the model

Because input data is large, the actual model including this data is not part of this repository. To use the model, you first need to generate it from input data and scripts. Running the generation step will generate the model in the `./model` folder.

    snakemake --use-conda

## Run on Euler cluster

To run on Euler, use the following command:

    snakemake --use-conda --profile config/euler

If you want to run on another cluster, read [snakemake's documentation on cluster execution](https://snakemake.readthedocs.io/en/stable/executable.html#cluster-execution) and take `config/euler` as a starting point.

## Example use of the model

The generation step created all single parts of `euro-calliope`, like technologies and time series. These can be combined to eventually build a final model to run simulations with. For an example of such a model, see `./tests/resources/national/connected-model.yaml`. It is a complete Calliope model and can be used like any other, for example like this:

```Bash
$ calliope run ./tests/resources/national/connected-model.yaml
```

For more information on how to use Calliope models, see [Calliope's documentation](https://www.callio.pe).

## Units and scaling

The default units used within euro-calliope are `100 GW`, `100 GWh`, `billion EUR`, and `10,000 km2`. All data going into Calliope and all Calliope result data will be given using these units. While they may be unusual, these units lead to a numerical model that is well suited for the interior-point solution algorithm that is used by default. The units are tuned so as to work best for models with a time resolution of a few hours and a duration of one year. For other types of problems, or other solution algorithms, the units may need to be changed to avoid numerical issues within the solver.

You can easily change the units and scale all values using the `scaling-factor` configuration values in `config/default.yaml`. However, these values must be changed before building the model. You may want to run `snakemake clean` before changing these values. The base units on which the scaling factors are applied are `1 MW`, `1 MWh`, `EUR`, and `km2`. So for example, the default unit for energy (100 GWh) is derived by scaling the base unit (1 MWh) with a scaling factor of `0.00001`.

## Repo structure

* `build/model`: contains the entire model after the generation step, including Calliope definition files and data (does not exist initially)
* `src`: contains the source data and source code to generate the model
* `envs`: contains files defining the environment to run the built steps in
* `tests`: contains a test usage of the model

## Run the tests

Tests of models with continental and national resolution run automatically when you run the entire workflow. To run the tests of models with regional resolution do the following:

    snakemake --use-conda build/logs/regional/test-report.html

Exchanging `regional` with `national` or `continental` allows you to run tests on the respective resolution explicitly.