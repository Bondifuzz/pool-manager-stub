from prometheus_client.metrics import Gauge

pools_unreleased_desc = "Count of pools with unreleased resources. Must be 0"
pools_unreleased = Gauge("pools_unreleased", pools_unreleased_desc)
