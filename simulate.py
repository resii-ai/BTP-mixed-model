# Movie theatre simulation
#Reduce wait time for customer
# arrive 
#get in line
# buy ticket
# get ticket checked
#buy food or no


import simpy 
import random 
import statistics


class Guitar_Factory:
    def __init__(self, env):
        self.wood = simpy.Container(env, capacity = wood_capacity, init = initial_wood)
        self.wood_control = env.process(self.wood_stock_control(env))
        self.electronic = simpy.Container(env, capacity = electronic_capacity, init = initial_electronic)
        self.electronic_control = env.process(self.electronic_stock_control(env))
        self.body_pre_paint = simpy.Container(env, capacity = body_pre_paint_capacity, init = 0)
        self.neck_pre_paint = simpy.Container(env, capacity = neck_pre_paint_capacity, init = 0)
        self.body_post_paint = simpy.Container(env, capacity = body_post_paint_capacity, init = 0)
        self.neck_post_paint = simpy.Container(env, capacity = neck_post_paint_capacity, init = 0)
        self.dispatch = simpy.Container(env ,capacity = dispatch_capacity, init = 0)
        self.dispatch_control = env.process(self.dispatch_guitars_control(env))

        
    def wood_stock_control(self, env):
        yield env.timeout(0)
        while True:
            if self.wood.level <= wood_critial_stock:
                print('wood stock bellow critical level ({0}) at day {1}, hour {2}'.format(
                    self.wood.level, int(env.now/8), env.now % 8))
                print('calling wood supplier')
                print('----------------------------------')
                yield env.timeout(16)
                print('wood supplier arrives at day {0}, hour {1}'.format(
                    int(env.now/8), env.now % 8))
                yield self.wood.put(300)
                print('new wood stock is {0}'.format(
                    self.wood.level))
                print('----------------------------------')
                yield env.timeout(8)
            else:
                yield env.timeout(1)
    
    def electronic_stock_control(self, env):
        yield env.timeout(0)
        while True:
            if self.electronic.level <= electronic_critical_stock:
                print('electronic stock bellow critical level ({0}) at day {1}, hour {2}'.format(
                    self.electronic.level, int(env.now/8), env.now % 8))
                print('calling electronic supplier')
                print('----------------------------------')
                yield env.timeout(9)
                print('electronic supplier arrives at day {0}, hour {1}'.format(
                    int(env.now/8), env.now % 8))
                yield self.electronic.put(30)
                print('new electronic stock is {0}'.format(
                    self.electronic.level))
                print('----------------------------------')
                yield env.timeout(8)
            else:
                yield env.timeout(1)
                
    def dispatch_guitars_control(self, env):
        global guitars_made
        yield env.timeout(0)
        while True:
            if self.dispatch.level >= 50:
                print('dispach stock is {0}, calling store to pick guitars at day {1}, hour {2}'.format(
                    self.dispatch.level, int(env.now/8), env.now % 8))
                print('----------------------------------')
                yield env.timeout(4)
                print('store picking {0} guitars at day {1}, hour {2}'.format(
                    self.dispatch.level, int(env.now/8), env.now % 8))
                guitars_made += self.dispatch.level
                yield self.dispatch.get(self.dispatch.level)
                print('----------------------------------')
                yield env.timeout(8)
            else:
                yield env.timeout(1)

def body_maker(env, guitar_factory):
    while True:
        yield guitar_factory.wood.get(1)
        body_time = random.gauss(mean_body, std_body)
        yield env.timeout(body_time)
        yield guitar_factory.body_pre_paint.put(1)

def neck_maker(env, guitar_factory):
    while True:
        yield guitar_factory.wood.get(1)
        neck_time = random.gauss(mean_neck, std_neck)
        yield env.timeout(neck_time)
        yield guitar_factory.neck_pre_paint.put(2)
        
def painter(env, guitar_factory):
    while True:
        yield guitar_factory.body_pre_paint.get(5)
        yield guitar_factory.neck_pre_paint.get(5)
        paint_time = random.gauss(mean_paint, std_paint)
        yield env.timeout(paint_time)
        yield guitar_factory.body_post_paint.put(5)
        yield guitar_factory.neck_post_paint.put(5)

def assembler(env, guitar_factory):
    while True:
        yield guitar_factory.body_post_paint.get(1)
        yield guitar_factory.neck_post_paint.get(1)
        yield guitar_factory.electronic.get(1)
        assembling_time = max(random.gauss(mean_ensam, std_ensam), 1)
        yield env.timeout(assembling_time)
        yield guitar_factory.dispatch.put(1)
        
        
#Generators
        
def body_maker_gen(env, guitar_factory):
    for i in range(num_body):
        env.process(body_maker(env, guitar_factory))
        yield env.timeout(0)

def neck_maker_gen(env, guitar_factory):
    for i in range(num_neck):
        env.process(neck_maker(env, guitar_factory))
        yield env.timeout(0)

def painter_maker_gen(env, guitar_factory):
    for i in range(num_paint):
        env.process(painter(env, guitar_factory))
        yield env.timeout(0)

def assembler_maker_gen(env, guitar_factory):
    for i in range(num_ensam):
        env.process(assembler(env, guitar_factory))
        yield env.timeout(0)


class Theater(object):
    def __init__(self, env, num_cashiers, num_servers, num_ushers):
        self.env = env
        self.cashier = simpy.Resource(env, num_cashiers)
        self.server = simpy.Resource(env, num_servers)
        self.usher = simpy.Resource(env, num_ushers)

    def purchase_ticket(self, moviegoer):
        yield self.env.timeout(random.randint(1, 3))

    def check_ticket(self, moviegoer):
        yield self.env.timeout(3 / 60)

    def sell_food(self, moviegoer):
        yield self.env.timeout(random.randint(1, 5))


wait_times = []

def go_to_movies(env, moviegoer, theater):
    # Moviegoer arrives at the theater
    arrival_time = env.now

    with theater.cashier.request() as request:
        yield request
        yield env.process(theater.purchase_ticket(moviegoer))

    with theater.usher.request() as request:
        yield request
        yield env.process(theater.check_ticket(moviegoer))

    if random.choice([True, False]):
        with theater.server.request() as request:
            yield request
            yield env.process(theater.sell_food(moviegoer))

    # Moviegoer heads into the theater
    wait_times.append(env.now - arrival_time)


def run_theater(env, num_cashiers, num_servers, num_ushers):
    theater = Theater(env, num_cashiers, num_servers, num_ushers)

    for moviegoer in range(3):
        env.process(go_to_movies(env, moviegoer, theater))

    while True:
        yield env.timeout(0.20)  # Wait a bit before generating a new person

        moviegoer += 1
        env.process(go_to_movies(env, moviegoer, theater))


def get_average_wait_time(wait_times):
    average_wait = statistics.mean(wait_times)
    # Pretty print the results
    minutes, frac_minutes = divmod(average_wait, 1)
    seconds = frac_minutes * 60
    return round(minutes), round(seconds)


def get_user_input():
    num_cashiers = input("Input # of cashiers working: ")
    num_servers = input("Input # of servers working: ")
    num_ushers = input("Input # of ushers working: ")
    params = [num_cashiers, num_servers, num_ushers]
    if all(str(i).isdigit() for i in params):  # Check input is valid
        params = [int(x) for x in params]
    else:
        print(
            "Could not parse input. Simulation will use default values:",
            "\n1 cashier, 1 server, 1 usher.",
        )
        params = [1, 1, 1]
    return params



# def guitar_wait_time():
    
    
    env = simpy.Environment()
    guitar_factory = Guitar_Factory(env)


    body_gen = env.process(body_maker_gen(env, guitar_factory))
    neck_gen = env.process(neck_maker_gen(env, guitar_factory))
    painter_gen = env.process(painter_maker_gen(env, guitar_factory))
    assembler_gen = env.process(assembler_maker_gen(env, guitar_factory))

    env.run(until = total_time)


    print('Pre paint has {0} bodies and {1} necks ready to be painted'.format(
        guitar_factory.body_pre_paint.level, guitar_factory.neck_pre_paint.level))
    print('Post paint has {0} bodies and {1} necks ready to be assembled'.format(
        guitar_factory.body_post_paint.level, guitar_factory.neck_post_paint.level))
    print(f'Dispatch has %d guitars ready to go!' % guitar_factory.dispatch.level)
    print(f'----------------------------------')
    print('total guitars made: {0}'.format(guitars_made + guitar_factory.dispatch.level))
    print(f'----------------------------------')
    print(f'SIMULATION COMPLETED')



def cinema_wait_time():
    # Setup
    random.seed(42)
    num_cashiers, num_servers, num_ushers = get_user_input()

    # Run the simulation
    env = simpy.Environment()
    env.process(run_theater(env, num_cashiers, num_servers, num_ushers))
    env.run(until=90)

    # View the results
    mins, secs = get_average_wait_time(wait_times)
    print(
        "Running simulation...",
        f"\nThe average wait time is {mins} minutes and {secs} seconds.",
    )




if __name__ == "__main__":
    # main()
    options = {1: ["Food and Entertainment", "Theatre", "Restaurant"], 2: ["Manufacturing", "Musical Instrument", "Vehicle"]}
    for key in options.keys():
        print(f"{key}.: {options[key][0]}")

    inp = int(input("Which simulation do you want to perform?:"))
    # return res

    # inp = opt()
    print(f"Selected input is {inp}.: {options[key][0]}")
    # ans = input("Do you want to proceed with the current choice? (Y/N)")

    # if ans == "Y":
    #     continue 
    # else:


    if inp == 1:
        print(f"Selected choice is: {inp} - {options[inp][0]}")
        print("Choose you category:")
        for i in range(1,3):
            print(f"{i}: {options[inp][i]}")
        
        select = int(input("Your choice: "))
        print(f"Your selected choice is: {options[inp][select]}")
        if select == 1:
            cinema_wait_time()
        
        elif select == 2:
            #food
            pass
        else:
            print("Invalid input, please try again")



    if inp == 2:
        print(f"Selected choice is: {inp} - {options[inp][0]}")
        print("Choose you category:")
        for i in range(1,3):
            print(f"{i}: {options[inp][i]}")
        
        select = int(input("Your choice: "))
        print(f"Your selected choice is: {options[inp][select]}")
        if select == 1:
            guitars_made = 0
            print(f'STARTING SIMULATION')
            print(f'----------------------------------')

            #-------------------------------------------------

            #Parameters

            #working hours
            hours = 8

            #business days
            days = 23

            #total working time (hours)
            total_time = hours * days

            #containers
                #wood
            wood_capacity = 500
            initial_wood = 200

                #electronic
            electronic_capacity = 100
            initial_electronic = 60

                #paint
            body_pre_paint_capacity = 60
            neck_pre_paint_capacity = 60
            body_post_paint_capacity = 120
            neck_post_paint_capacity = 120
                
                #dispatch
            dispatch_capacity = 500


            #employees per activity
                #body
            num_body = 2
            mean_body = 1
            std_body = 0.1

                #neck
            num_neck = 1
            mean_neck = 1
            std_neck = 0.2

                #paint
            num_paint = 3
            mean_paint = 3
            std_paint = 0.3

                #ensambling
            num_ensam = 2
            mean_ensam = 1
            std_ensam = 0.2


            #critical levels
                #critical stock should be 1 business day greater than supplier take to come
            wood_critial_stock = (((8/mean_body) * num_body +
                                (8/mean_neck) * num_neck) * 3) #2 days to deliver + 1 marging

            electronic_critical_stock = (8/mean_ensam) * num_ensam * 2 #1 day to deliver + 1 marging
            
            env = simpy.Environment()
            guitar_factory = Guitar_Factory(env)


            body_gen = env.process(body_maker_gen(env, guitar_factory))
            neck_gen = env.process(neck_maker_gen(env, guitar_factory))
            painter_gen = env.process(painter_maker_gen(env, guitar_factory))
            assembler_gen = env.process(assembler_maker_gen(env, guitar_factory))

            env.run(until = total_time)


            print('Pre paint has {0} bodies and {1} necks ready to be painted'.format(
                guitar_factory.body_pre_paint.level, guitar_factory.neck_pre_paint.level))
            print('Post paint has {0} bodies and {1} necks ready to be assembled'.format(
                guitar_factory.body_post_paint.level, guitar_factory.neck_post_paint.level))
            print(f'Dispatch has %d guitars ready to go!' % guitar_factory.dispatch.level)
            print(f'----------------------------------')
            print('total guitars made: {0}'.format(guitars_made + guitar_factory.dispatch.level))
            print(f'----------------------------------')
            print(f'SIMULATION COMPLETED')



        elif select == 2:
            #cars
            pass
        else:
            print("Invalid input, please try again")

        