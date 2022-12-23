import "date"

option task = {name: "Calculate Latency", every: 5m}

from(bucket: "ThermometerRecords")
    |> range(start: -duration(v: int(v: task.every) + int(v: 1m)))
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
