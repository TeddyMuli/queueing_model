#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define Q_LIMIT 100
#define BUSY    1
#define IDLE    0

/* Function prototypes */
void initialize(void);
void timing(void);
void arrive(void);
void depart(void);
void report(void);
void update_time_avg_stats(void);
float expon(float mean);
float lcgrand(int stream);

/* Global variables */
int next_event_type, num_custs_delayed, num_delays_required, num_events, num_in_q, server_status;
float area_num_in_q, area_server_status, mean_interarrival, mean_service, sim_time;
float time_arrival[Q_LIMIT + 1], time_last_event, time_next_event[3], total_of_delays;
FILE *infile, *outfile;

int main()
{
    /* Open input and output files */
    infile = fopen("mml.in", "r");
    if (infile == NULL) {
        printf("Error: Cannot open input file 'mml.in'\n");
        return 1;
    }
    
    outfile = fopen("mml.out", "w");
    if (outfile == NULL) {
        printf("Error: Cannot open output file 'mml.out'\n");
        fclose(infile);
        return 1;
    }

    /* Number of events for timing function */
    num_events = 2;

    /* Read input parameters */
    if (fscanf(infile, "%f %f %d", &mean_interarrival, &mean_service, &num_delays_required) != 3) {
        printf("Error: Invalid input file format\n");
        fclose(infile);
        fclose(outfile);
        return 1;
    }
    
    /* Write report heading and input parameters */
    fprintf(outfile, "Single-server queueing system\n\n");
    fprintf(outfile, "Mean interarrival time%11.3f minutes\n\n", mean_interarrival);
    fprintf(outfile, "Mean service time%16.3f minutes\n\n", mean_service);
    fprintf(outfile, "Number of customers%14d\n\n", num_delays_required);

    /* Initialize simulation */
    initialize();

    /* Run the simulation while more delays are still needed */
    while (num_custs_delayed < num_delays_required) {
        /* Determine the next events */
        timing();
        
        /* Update time-average statistical accumulators */
        update_time_avg_stats();

        /* Invoke the appropriate event function */
        switch (next_event_type) {
            case 1:
                arrive();
                break;
            case 2:
                depart();
                break;
        }
    }

    report();

    fclose(infile);
    fclose(outfile);

    return 0;
}

void initialize(void)
{
    /* Initialize simulation clock */
    sim_time = 0.0;

    server_status   = IDLE;
    num_in_q        = 0;
    time_last_event = 0.0;

    /* Initialize statistical counters */
    num_custs_delayed  = 0;
    total_of_delays    = 0.0;
    area_num_in_q      = 0.0;
    area_server_status = 0.0;

    /* Initialize event list */
    time_next_event[1] = sim_time + expon(mean_interarrival);
    time_next_event[2] = 1.0e+30;
}

void timing(void)
{
    int i;
    float min_time_next_event = 1.0e+29;

    next_event_type = 0;

    /* Determine the event type of the next event to occur */
    for (i = 1; i <= num_events; ++i) {
        if (time_next_event[i] < min_time_next_event) {
            min_time_next_event = time_next_event[i];
            next_event_type = i;
        }
    }

    /* Check to see whether the event list is empty */
    if (next_event_type == 0) {
        /* The event list is empty, so stop simulation */
        fprintf(outfile, "\nEvent list empty at time %f", sim_time);
        exit(1);
    }

    /* The event list is not empty, so advance the simulation clock */
    sim_time = min_time_next_event;
}

void arrive(void)
{
    float delay;
    
    /* Schedule next arrival */
    time_next_event[1] = sim_time + expon(mean_interarrival);
    
    /* Check to see if server is busy */
    if (server_status == BUSY) {
        /* Server is busy, so increment number of customers in queue */
        ++num_in_q;
        
        /* Check to see whether an overflow condition exists */
        if (num_in_q > Q_LIMIT) {
            /* The queue has overflowed, so stop the simulation */
            fprintf(outfile, "\nOverflow of the array time_arrival at time %f", sim_time);
            fclose(infile);
            fclose(outfile);
            exit(2);
        }

        /* There is still room in the queue, so store the time of arrival */
        time_arrival[num_in_q] = sim_time;
    } else {
        /* Server is idle, so arriving customer has a delay of zero */
        delay = 0.0;
        total_of_delays += delay;

        /* Increment the number of customers delayed, and make server busy */
        ++num_custs_delayed;
        server_status = BUSY;

        /* Schedule a departure (service completion) */
        time_next_event[2] = sim_time + expon(mean_service);
    }
}

void depart(void)
{
    int i;
    float delay;

    /* Check to see if the queue is empty */
    if (num_in_q == 0) {
        /* The queue is empty so make the server idle and eliminate departures */
        server_status = IDLE;
        time_next_event[2] = 1.0e+30;
    } else {
        /* The queue is nonempty, so decrement number of customers in queue */
        --num_in_q;

        /* Compute the delay of the customer who is beginning service and update total delay */
        delay = sim_time - time_arrival[1];
        total_of_delays += delay;

        /* Increment the number of customers delayed, and schedule departure */
        ++num_custs_delayed;
        time_next_event[2] = sim_time + expon(mean_service);

        /* Move each customer in queue up one place */
        for (i = 1; i <= num_in_q; ++i) {
            time_arrival[i] = time_arrival[i + 1];
        }
    }
}

void report(void)
{
    /* Compute and write estimates of desired measures of performance */
    fprintf(outfile, "\n\nAverage delay in queue%11.3f minutes\n\n",
            total_of_delays / num_custs_delayed);
    fprintf(outfile, "Average number in queue%10.3f\n\n",
            area_num_in_q / sim_time);
    fprintf(outfile, "Server utilization%15.3f\n\n",
            area_server_status / sim_time);
    fprintf(outfile, "Time simulation ended%12.3f minutes", sim_time);
}

void update_time_avg_stats(void)
{
    float time_since_last_event;
    
    /* Compute time since last event, and update last-event-time marker */
    time_since_last_event = sim_time - time_last_event;
    time_last_event = sim_time;
    
    /* Update area under number-in-queue function */
    area_num_in_q += num_in_q * time_since_last_event;
    
    /* Update area under server-busy indicator function */
    area_server_status += server_status * time_since_last_event;
}

float expon(float mean)
{
    /* Return an exponential random variate with mean "mean" */
    return -mean * log(lcgrand(1));
}

float lcgrand(int stream)
{
    /* Simple implementation of a random number generator */
    static int initialized = 0;
    
    if (!initialized) {
        srand((unsigned int)time(NULL));
        initialized = 1;
    }
    
    return (float)rand() / RAND_MAX;
}
