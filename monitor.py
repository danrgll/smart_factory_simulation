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

        for name in ['request']:
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
    def __init__(self, env: simpy.Environment, id, monitor_event):
        self.env = env
        self.product_id = id
        self.monitor_event = monitor_event
        self.process_steps = ["base_element provided", "ring_elements mounted", "cap_element mounted", "delivered"]
        self.data = []
        self.file = open("product" + str(self.product_id) + ".txt", "w")
        self.file.write(f"Manufacturing log of product {str(self.product_id)}: \n")
        self.env.process(self.monitor())

    def monitor(self):
        i = 0
        while i <= 3:
            print("testtooto")
            yield self.monitor_event.event
            self.file.write(f"{self.process_steps[i]} at time {self.env.now} \n")
            self.data.append(self.env.now)
            i += 1
        # self.log_book("product" + str(self.product_id))
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
