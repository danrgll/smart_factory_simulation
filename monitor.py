import simpy
from functools import wraps
from base_elements import Event


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
        """Each time a resource is released again, information about monitor_resource is stored."""
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
    """Monitors the production process of a product and save the information in a file"""
    def __init__(self, env: simpy.Environment, id):
        self.env = env
        self.product_id = id
        self.current_machine = None
        self.monitor_event = Event(self.env)
        self.data = []
        # commented out for evaluation.
        # self.file = open("product" + str(self.product_id) + ".txt", "w")
        # self.file.write(f"Manufacturing log of product {str(self.product_id)}: \n")
        # self.file.close()

    def monitor(self, mode, time, location, id=None):
        """Writes observed information to the file"""
        # commented out for evaluation.
        # self.log_all = open("log_all.txt", "a")
        # self.file = open("product" + str(self.product_id) + ".txt", "a")
        if id is not None:
            pass
            # self.file.write(f"{location} {id} at time {time}, mode: {mode}\n")
            # self.log_all.write(f"{location} {id} at time {time}, mode: {mode}\n")
        else:
            pass
            # self.file.write(f"{location} at time {time}, mode: {mode}\n")
            # self.log_all.write(f"{location} at time {time}, mode: {mode}\n")
        self.data.append(time)
        # self.file.close()


class MonitorDestination:
    def __init__(self):
        self.data = []

    def monitor_process(self, product, time):
        self.data.append([product.order_number, time])
