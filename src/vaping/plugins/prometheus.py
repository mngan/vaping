from prometheus_client import Counter, Gauge, Summary, start_http_server

import vaping
import vaping.plugins
from pprint import pformat

min_latency = Summary(
    "minimum_latency_milliseconds", "Minimum latency in milliseconds.", ["host", "target"]
)  # NOQA
max_latency = Summary(
    "maximum_latency_milliseconds", "Maximum latency in milliseconds.", ["host", "target"]
)  # NOQA
avg_latency = Summary(
    "average_latency_milliseconds", "Average latency in milliseconds.", ["host", "target"]
)  # NOQA
sent_packets = Counter(
    "number_of_packets_sent", "Number of pings sent to host.", ["host", "target"]
)  # NOQA
packet_loss = Gauge("packet_loss", "% packet loss to host (0-100)", ["host", "target"])  # NOQA


@vaping.plugin.register("prometheus")
class Prometheus(vaping.plugins.EmitBase):
    def init(self):
        self.log.debug("init prometheus plugin")
        port = self.pluginmgr_config.get("port", 9099)
        start_http_server(port)

    def emit(self, data):
        raw_data = data.get("data")

        for host_data in raw_data:
            if host_data is None:
                continue
            if isinstance(host_data.get('data'), dict):
                data = []
                for k, v in host_data['data'].items():
                    v['host'] =  k
                    v['target'] = host_data['host']
                    data.append(v)
                self.emit(dict(data=data))
                continue

            self.log.debug("DATA: " + pformat(host_data))

            host_name = host_data.get("host")
            target = host_data.get('target')
            if "min" in host_data:
                min_latency.labels(host_name, target).observe(host_data.get("min"))
            if "max" in host_data:
                max_latency.labels(host_name, target).observe(host_data.get("max"))
            if "avg" in host_data:
                avg_latency.labels(host_name, target).observe(host_data.get("avg"))
            sent_packets.labels(host_name, target).inc(host_data.get("cnt"))
            packet_loss.labels(host_name, target).set(host_data.get("loss") * 100)
