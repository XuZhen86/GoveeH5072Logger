import "date"

option task = {name: "Backfill Latency", every: 1y}

from(bucket: "ThermometerRecords")
    |> range(start: -task.every)
    |> filter(fn: (r) => r["_measurement"] == "temperature")
    |> sort(columns: ["_time"])
    |> map(fn: (r) => ({r with _value: int(v: r["_time"]), _measurement: "latency", _field: "latency_ns"}))
    |> difference()
    |> map(fn: (r) => ({r with _time: date.sub(d: duration(v: r["_value"]), from: r["_time"])}))
    |> keep(
        columns: [
            "_time",
            "_measurement",
            "_field",
            "_value",
            "device_name",
            "nick_name",
        ],
    )
    |> to(bucket: "ThermometerRecordsDerived", org: "Organization")
