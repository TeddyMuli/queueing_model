import math
import random
import time

# Constants
Q_LIMIT = 100
BUSY = 1
IDLE = 0

class QueueSimulation:
    def __init__(self, mean_interarrival, mean_service, num_delays_required):
        # Simulation parameters
        self.mean_interarrival = mean_interarrival
        self.mean_service = mean_service
        self.num_delays_required = num_delays_required
        self.num_events = 2
        
        # State variables
        self.next_event_type = 0
        self.num_custs_delayed = 0
        self.num_in_q = 0
        self.server_status = IDLE
        self.sim_time = 0.0
        self.time_arrival = [0.0] * (Q_LIMIT + 1)
        self.time_last_event = 0.0
        self.time_next_event = [0.0, 0.0, 0.0]  # Index 0 not used
        self.total_of_delays = 0.0
        self.area_num_in_q = 0.0
        self.area_server_status = 0.0
        
        # Output file
        self.outfile = open("mml_python.out", "w")
        
        # Initialize random number generator
        random.seed(int(time.time()))
    
    def initialize(self):
        # Initialize simulation clock
        self.sim_time = 0.0
        
        self.server_status = IDLE
        self.num_in_q = 0
        self.time_last_event = 0.0
        
        # Initialize statistical counters
        self.num_custs_delayed = 0
        self.total_of_delays = 0.0
        self.area_num_in_q = 0.0
        self.area_server_status = 0.0
        
        # Initialize event list
        self.time_next_event[1] = self.sim_time + self.expon(self.mean_interarrival)
        self.time_next_event[2] = 1.0e+30
    
    def timing(self):
        min_time_next_event = 1.0e+29
        self.next_event_type = 0
        
        # Determine the event type of the next event to occur
        for i in range(1, self.num_events + 1):
            if self.time_next_event[i] < min_time_next_event:
                min_time_next_event = self.time_next_event[i]
                self.next_event_type = i
        
        # Check to see whether the event list is empty
        if self.next_event_type == 0:
            # The event list is empty, so stop simulation
            self.outfile.write(f"\nEvent list empty at time {self.sim_time}")
            exit(1)
        
        # The event list is not empty, so advance the simulation clock
        self.sim_time = min_time_next_event
    
    def arrive(self):
        # Schedule next arrival
        self.time_next_event[1] = self.sim_time + self.expon(self.mean_interarrival)
        
        # Check to see if server is busy
        if self.server_status == BUSY:
            # Server is busy, so increment number of customers in queue
            self.num_in_q += 1
            
            # Check to see whether an overflow condition exists
            if self.num_in_q > Q_LIMIT:
                # The queue has overflowed, so stop the simulation
                self.outfile.write(f"\nOverflow of the array time_arrival at time {self.sim_time}")
                self.outfile.close()
                exit(2)
            
            # There is still room in the queue, so store the time of arrival
            self.time_arrival[self.num_in_q] = self.sim_time
        else:
            # Server is idle, so arriving customer has a delay of zero
            delay = 0.0
            self.total_of_delays += delay
            
            # Increment the number of customers delayed, and make server busy
            self.num_custs_delayed += 1
            self.server_status = BUSY
            
            # Schedule a departure (service completion)
            self.time_next_event[2] = self.sim_time + self.expon(self.mean_service)
    
    def depart(self):
        # Check to see if the queue is empty
        if self.num_in_q == 0:
            # The queue is empty so make the server idle and eliminate departures
            self.server_status = IDLE
            self.time_next_event[2] = 1.0e+30
        else:
            # The queue is non-empty, so decrement number of customers in queue
            self.num_in_q -= 1
            
            # Compute the delay of the customer who is beginning service and update total delay
            delay = self.sim_time - self.time_arrival[1]
            self.total_of_delays += delay
            
            # Increment the number of customers delayed, and schedule departure
            self.num_custs_delayed += 1
            self.time_next_event[2] = self.sim_time + self.expon(self.mean_service)
            
            # Move each customer in queue up one place
            for i in range(1, self.num_in_q + 1):
                self.time_arrival[i] = self.time_arrival[i + 1]
    
    def report(self):
        # Compute and write estimates of desired measures of performance
        self.outfile.write("\n\nAverage delay in queue{:11.3f} minutes\n\n".format(
            self.total_of_delays / self.num_custs_delayed))
        self.outfile.write("Average number in queue{:10.3f}\n\n".format(
            self.area_num_in_q / self.sim_time))
        self.outfile.write("Server utilization{:15.3f}\n\n".format(
            self.area_server_status / self.sim_time))
        self.outfile.write("Time simulation ended{:12.3f} minutes".format(self.sim_time))
        self.outfile.close()
    
    def update_time_avg_stats(self):
        # Compute time since last event, and update last-event-time marker
        time_since_last_event = self.sim_time - self.time_last_event
        self.time_last_event = self.sim_time
        
        # Update area under number-in-queue function
        self.area_num_in_q += self.num_in_q * time_since_last_event
        
        # Update area under server-busy indicator function
        self.area_server_status += self.server_status * time_since_last_event
    
    def expon(self, mean):
        # Return an exponential random variate with mean "mean"
        return -mean * math.log(random.random())
    
    def run(self):
        # Write report heading and input parameters
        self.outfile.write("Single-server queueing system\n\n")
        self.outfile.write("Mean interarrival time{:11.3f} minutes\n\n".format(self.mean_interarrival))
        self.outfile.write("Mean service time{:16.3f} minutes\n\n".format(self.mean_service))
        self.outfile.write("Number of customers{:14d}\n\n".format(self.num_delays_required))
        
        # Initialize the simulation
        self.initialize()
        
        # Run the simulation while more delays are still needed
        while self.num_custs_delayed < self.num_delays_required:
            # Determine the next event
            self.timing()
            
            # Update time-average statistical accumulators
            self.update_time_avg_stats()
            
            # Invoke the appropriate event function
            if self.next_event_type == 1:
                self.arrive()
            elif self.next_event_type == 2:
                self.depart()
        
        # Generate the report
        self.report()

def main():
    # Read input parameters
    try:
        with open("mml.in", "r") as infile:
            params = infile.readline().split()
            if len(params) < 3:
                raise ValueError("Input file must contain three values")
            
            mean_interarrival = float(params[0])
            mean_service = float(params[1])
            num_delays_required = int(params[2])
    except FileNotFoundError:
        print("Error: Cannot open input file 'mml.in'")
        print("Creating default input parameters...")
        mean_interarrival = 5.0
        mean_service = 3.0
        num_delays_required = 1000
        
        # Create default input file
        with open("mml.in", "w") as infile:
            infile.write(f"{mean_interarrival} {mean_service} {num_delays_required}")
        print(f"Created mml.in with values: {mean_interarrival} {mean_service} {num_delays_required}")
    
    # Create and run the simulation
    sim = QueueSimulation(mean_interarrival, mean_service, num_delays_required)
    sim.run()
    print("Simulation complete. Results written to mml_python.out")

if __name__ == "__main__":
    main()

