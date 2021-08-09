# Model overview

No matter whether you have downloaded Euro-Calliope's pre-builts or you have built the models yourself successfully, you will have a set of files in front of you. Let's make sense of these files.

## File structure

By default, Euro-Calliope is a set of three models on different spatial resolutions: continental, national, and regional.
All files that depend on the spatial resolution are within subfolders named by the resolution.
All files in the root directory are independent of the spatial resolution.

```
├── {resolution}                           <- For each spatial resolution an individual folder.
│   ├── capacityfactors-{technology}.csv   <- Timeseries of capacityfactors of all renewables.
│   ├── directional-rooftop.yaml           <- Override discriminating rooftop PV by orientation.
│   ├── electricity-demand.csv             <- Timeseries of electricity demand on each node.
│   ├── example-model.yaml                 <- Calliope model definition.
│   ├── link-all-neighbours.yaml           <- Connects neighbouring locations with transmission.
│   ├── entsoe-tyndp-links.yaml            <- Connects regions according to ENTSO-E; exists only if resolution = "national".
│   ├── load-shedding.yaml                 <- Override adding option to shed load.
│   ├── locations.csv                      <- Map from Calliope location id to name of location.
│   └── locations.yaml                     <- Defines all locations and their max capacities.
├── build-metadata.yaml                    <- Metadata of the build process.
├── demand-techs.yaml                      <- Definition of demand technologies.
├── environment.yaml                       <- Conda file defining an environment to run the model in.
├── interest-rate.yaml                     <- Interest rates of all capacities.
├── link-techs.yaml                        <- Definition of link technologies.
├── README.md                              <- Basic documentation (pre-builts only).
├── tech-costs.yaml                        <- Definition of cost data.
├── renewable-techs.yaml                   <- Definition of supply technologies.
└── storage-techs.yaml                     <- Definition of storage technologies.
```

## Units of quantities

The units of quantities within the models are the following:

* power: 100 GW
* energy: 100 GWh
* area: 10,000 km²
* monetary cost: billion EUR

All data going into Calliope and all Calliope result data will be given using these units.
While they may be unusual, these units lead to a numerical model that is well suited for the interior-point solution algorithm that is used by default.
The units are tuned so as to work best for models with a time resolution of a few hours and a duration of one year.
For other types of problems, or other solution algorithms, the units may need to be changed to avoid numerical issues within the solver.

When you run the workflow, you can easily change the units and scale all values using the `scaling-factor` configuration parameters, see [Configuration](./customisation.md#configuration).
The base units on which the scaling factors are applied are `1 MW`, `1 MWh`, `EUR`, and `km2`.
So for example, the default unit for energy (100 GWh) is derived by scaling the base unit (1 MWh) with a scaling factor of `0.00001`.

## Components and assumptions

For an in-depth description of all model components and the data preprocessing steps, please read the [open-access article introducing Euro-Calliope in Joule](https://doi.org/10.1016/j.joule.2020.07.018).