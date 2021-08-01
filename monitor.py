import simpy
from functools import wraps


class MonitorResource:
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

        for name in ['put', 'get', 'request', 'release']:
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
        log_data = self.data
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
    def __init__(self, env: simpy.Environment, product_id, events: dict):
        self.env = env
        self.product_id = product_id
        self.events = events
        self.data = []
        self.env.process(self.monitor())

    def monitor(self):
        if "base_station" in self.events:
            yield self.events["base_station"].event
            self.data.append(self.env.now)
        if "ring_station" in self.events:
            yield self.events["ring_station"].event
            self.data.append(self.env.now)
        if "cap_station" in self.events:
            yield self.events["cap_station"].event
            self.data.append(self.env.now)
        if "del_station" in self.events:
            yield self.events["del_station"].event
            self.data.append(self.env.now)
        if "completed" in self.events:
            yield self.events["completed"].event
            self.data.append(self.env.now)
        self.log_book("product" + str(self.product_id))

    def log_book(self, file: str):
        log_data = self.data
        log_data.reverse()
        with open(file, "w") as fobj:
            fobj.write(f"Manufacturing log of product {str(self.product_id)}: \n")
            while True:
                try:
                    item = log_data.pop()
                    fobj.write(f"process step completed at time {item} \n")
                except IndexError:
                    break
