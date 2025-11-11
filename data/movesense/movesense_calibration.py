# This file was automatically generated on 2025-11-06T21:22:15
calibration_data = {
    "device": "MoveSense",
    "created_at": "2025-11-06T21:22:15",
    "sensors": {
        "accelerometer": {
            "bias": {
                "X": -0.014147499999999091,
                "Y": -0.04961500000000019,
                "Z": 0.035102499999999814
            },
            "scale": {
                "X": 1.0073957696228337,
                "Y": 1.007814475025484,
                "Z": 1.0144518348623854
            },
            "source_file": [
                "../../data/movesense/calib/filtered/up(calib-1)_filtered.csv",
                "../../data/movesense/calib/filtered/down(calib-2)_filtered.csv",
                "../../data/movesense/calib/filtered/right(calib-3)_filtered.csv",
                "../../data/movesense/calib/filtered/left(calib-4)_filtered.csv",
                "../../data/movesense/calib/filtered/back(calib-5)_filtered.csv",
                "../../data/movesense/calib/filtered/front(calib-6)_filtered.csv"
            ]
        },
        "gyroscope": {
            "bias": {
                "X": 0.07823249999999983,
                "Y": -0.12882666666666687,
                "Z": -0.09623416666666644
            },
            "source_file": [
                "../../data/movesense/calib/filtered/up(calib-1)_filtered.csv",
                "../../data/movesense/calib/filtered/down(calib-2)_filtered.csv",
                "../../data/movesense/calib/filtered/right(calib-3)_filtered.csv",
                "../../data/movesense/calib/filtered/left(calib-4)_filtered.csv",
                "../../data/movesense/calib/filtered/back(calib-5)_filtered.csv",
                "../../data/movesense/calib/filtered/front(calib-6)_filtered.csv"
            ]
        },
        "magnetometer": {
            "hard_iron_bias": [
                -32.947807,
                -26.394453,
                14.020047
            ],
            "soft_iron_scale": [
                0.807283,
                0.982248,
                1.176215
            ],
            "mean_field_before_uT": 140.042,
            "mean_field_after_uT": 147.615,
            "source_file": "magn_data_test_last3_filtered.csv"
        }
    }
}
