from VyPR.QueryBuilding import *
verification_conf = \
{
    ## Server side spec
     "src.main" : {
        "add" : [
            Forall(
                t = calls('check')
            ).Check(
                lambda t : (
                    t.duration()._in([0, 5])
                )
            )
        ]

    }
}
