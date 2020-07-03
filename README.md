# godon
(ancient ger.  = improving, rearranging, rendering benign)

![Logo](https://github.com/cherusk/godon/blob/master/logo.svg?sanitize=true)

# Objective

Generic, GEA multi objective obtimization techs wielding solution focussing on
online optimizing, rearranging, calibrating of technologies in need for it
throughout the stack.

# Principle Outline

Idea is to run a continuous or periodic optimization cycle. Ideally, there
should be a breeding sub landscape, where the GEAs can do their optimiziation
part in a safe, non-invasive or even disruptive way. Replicating load or
traffic patterns in such a replicate might appear challenging, but may not be
necessary. A proper enough approximation might suffice for the larger fraction
of practical use cases.

The optimizer core is working on DEAP workers parallelized with help of a shim
layer over commonplace distributed system orchestrator solutions. Further, the
feed-back control loop is driven in jobs, perceiving aggregated telemetry and
data of similar character gathered from the targeted objects. Also direct
inspection of the breeding status has to be foreseen. After running the
optimization via parallelized GEAs, the outcome will be applied on the breeder.
This cycle will run until a customer defined acceptance or approximation
epsilon has been reached or an another, maybe time-bound termination kicks in.

Eventual outcome shall be a configuration perceived sufficiently optimal.  It
must be handed in structured way to the consumer, allowing him to apply the
breeding result at higher criticality or the actual optimization target at his
or her arbitration in the way most desired or applicable.

![Outline_online](https://github.com/cherusk/godon/blob/master/staged_structure.svg?sanitize=true)

Alternatively, customers will not be hampered from doing all the previously
outlined directly on productive stacks.  If the targeted sub-components are not
of utmost criticallity, that could be a frequent scenario to expect also.

It's a special case of the previously described anyways.

![Outline_staged](https://github.com/cherusk/godon/blob/master/online_structure.svg?sanitize=true)

# Flow Outline

![Flow](https://github.com/cherusk/godon/blob/master/engine_flow.svg?sanitize=true)

# Sponsors

Greatest esteem to:

* OSU Open Source Lab (https://osuosl.org) for bestowing generously with resources on their openstack infrastructure

* genesiscloud (https://www.genesiscloud.com/) for providing free GPU acceleration to the project

# References 

Bases and inspired by POC research done in [1][2] or and broader discussions[3] in public domain.

[1] https://www.researchgate.net/publication/327392488_Autonomous_Configuration_of_Network_Parameters_in_Operating_Systems_using_Evolutionary_Algorithms

[2] https://zilimeng.com/papers/decima-sigcomm19.pdf

[3] https://news.ycombinator.com/item?id=15892956

