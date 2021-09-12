import simpy
from functools import wraps
from base_elements import Event


class MonitorResource:
    # TODO: KOMPLETTE SCHEISE WENN MONITORINGN VON MASCHINEN WEIL KAPUTT GEHEN MIT RELEASE AUSLÖST,NEUES MONITORING,
    """monitor simpy resources"""
    def __init__(self, env: simpy.Environment, resource, call, ):
        self.env = env
        self.resource = resource
        self.data = []
        if call == "pre":
            self.patch_resource(self.resource, pre=self.monitor_resource)
        if call == "post":
            self.patch_resource(self.resource, post=self.monitor_resource)

    def patch_resource(self, resource, pre=None, post=None):
        def get_wrapper(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if pre:
                    pre(resource)
                ret = func(*args, **kwargs)
                if post:
                    post(resource)
                return ret
            return wrapper

        for name in ['release']:
            if hasattr(resource, name):
                setattr(resource, name, get_wrapper(getattr(resource, name)))

    def monitor_resource(self, resource: simpy.Resource):
        """ create item with desired information and transfer it to self.data"""
        item = (
            self.env.now,  # simulation_time
            resource.count,  # number of users
            resource.capacity,  # capacity of the resource
            len(resource.queue)  # The number of queued processes
        )
        self.data.append(item)

    def log_book(self, file: str):
        """write data from self.data readable into file"""
        print(self.data)
        log_data = self.data
        print(log_data)
        log_data.reverse()
        with open(file, "w") as fobj:
            while True:
                try:
                    item = log_data.pop()
                    fobj.write(f"{item[1]} of {item[2]} slots are allocated at time {item[0]}"
                               f". Number of queued processes: {item[3]}" + "\n")
                except IndexError:
                    break


class MonitorProduct:
    def __init__(self, env: simpy.Environment, id, proc_steps):
        self.env = env
        self.product_id = id
        self.current_machine = None
        self.monitor_event = Event(self.env)
        # Wir noch garnicht sinnvoll verwendet
        if proc_steps == "cc0":
            self.monitor_process_steps = ["base_element provided", "cap_element mounted", "delivered"]
        else:
            self.monitor_process_steps = ["base_element provided", "ring_elements mounted", "cap_element mounted", "delivered"]
        self.data = []
        self.file = open("product" + str(self.product_id) + ".txt", "w")
        self.file.write(f"Manufacturing log of product {str(self.product_id)}: \n")
        self.env.process(self.monitor())

    def monitor(self):
        i = 0
        while True:
            yield self.monitor_event.event
            self.file.write(f"{self.monitor_process_steps[i]} at time {self.env.now} \n")
            self.data.append(self.env.now)
            i += 1
        #self.log_book("product" + str(self.product_id))
        self.file.close()

    def log_book(self, file: str):
        log_data = self.data
        process_steps_copy = self.process_steps
        log_data.reverse()
        process_steps_copy.reverse()
        self.file.write(f"Manufacturing log of product {str(self.product_id)}: \n")
        while True:
            try:
                item = log_data.pop()
                proc = process_steps_copy.pop()
                self.file.write(f"{proc} at time {item} \n")
            except IndexError:
                break
        self.file.close()

class Monitor_Destination:
    def __init__(self):
        self.data = []
    def monitor_process(self, product, time):
        self.data.append([product.order_number, time])