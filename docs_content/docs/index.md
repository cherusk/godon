<!--
Copyright (c) 2019 Matthias Tafelmeier.

This file is part of godon

godon is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

godon is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this godon. If not, see <http://www.gnu.org/licenses/>.
-->

![Emblem](https://raw.githubusercontent.com/cherusk/godon/master/docs_content/logo.svg?sanitize=true)


## Introduction
-------------

This project approaches the problem of optimizing infrastructure technologies 
as a continuous multi objective combinatorial optimization problem in a dynamic environment

Meta-Heuristics, e.g. Evolutionary Algorithms (EA), have been found operating well in
such optimization problem fields.

Technologies throughout the stack are targeted. A focus is put on open technologies first.

Overall optimizing, rearranging, calibrating of technology settings throughout the life-cycle of an instance
of a technology are what is seeked to address with godon.

## Objective
-------------

### It is
-------------

* augmenting human operation engineers at bringing about performance improvements
    * it simplifies the process through standardization and industrialization
    * reduces prior knowledge needed about configuration changes and implications
    * less toil in terms of engineering hours spent
* tackles the wide spread neglection of broader performance tuning
* pragmatic operations engineering complementing instrument
* focussed on open technologies first
* approximating an optimal state in a dynamic environment changing over time
* leveraging metaheuristics algorithms of all kinds to explore combinatorial configuration spaces
* betting on parallelization and acceleration of metaheuristics

### It is not
-------------

* fully off-hands automation as human setup, supervision and planning is required
* a machine learning or data analysis oriented technology
    * kept to a minimum
    * ideally only used if needed in the implementation details of a metaheuristic
* guaranteeing a global optimum in the search space of configurations
    * rather approximating a better than untouched state
* a metaheuristics framework

## Sponsors
-------------

Greatest esteem to:

* OSU Open Source Lab (https://osuosl.org) for bestowing generously with resources on their openstack infrastructure

## References 
-------------

[1] Inspiring POC work for the project;[Autonomous_Configuration_of_Network_Parameters_in_Operating_Systems_using_Evolutionary_Algorithms](https://www.researchgate.net/publication/327392488_Autonomous_Configuration_of_Network_Parameters_in_Operating_Systems_using_Evolutionary_Algorithms)

[2] Underpinning the potential to accelerate metaheurstics by parallelization;[A unified view of parallel multi-objective evolutionary
algorithms](https://hal.archives-ouvertes.fr/hal-02304734/document)
