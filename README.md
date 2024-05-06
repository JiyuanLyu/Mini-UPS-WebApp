# Mini-UPS website

Developer: Chelsea (Jiyuan) Lyu - jl1230,
           Yijia Zhao - yz853

This project simulates an online store (Mini-Amazon) and a shipping service (Mini-UPS), requiring integration between the two systems within an interoperability group. The systems communicate with a simulated world server, handling logistics without real-world warehouses and trucks.

## Project Overview

- **Mini-Amazon**: Manages a virtual store where users can place orders. The system communicates with Mini-UPS to ensure deliveries are scheduled.
- **Mini-UPS**: Handles logistics and delivery of orders placed on Mini-Amazon, including managing trucks and their routes.

## Technical Details

- **Server Connection**: Connects to a simulation server at specified ports using the `.proto` files provided for Amazon and UPS.
- **Simulation World**: Each session is identified by a unique 64-bit world number. Operations are simulated on a Cartesian coordinate grid.
- **Operations**: Includes purchasing products, packing, loading shipments, and managing deliveries.


### Docker Set up

This project can be run in docker:

1. Make sure is under the `erss-project-yz853-jl1230/docker-deploy` directory

2. Edit the host port of the virtual machine address for Amazon and World Simulator in `docker-compose.yml`

3. Run `chmod +x myUPS/run.sh`

4. Run `sudo docker-compose down`

5. Run `sudo docker-compose up --build`

### `differentiation.txt` and `danger_log.txt`

These two files is located in the same directory with this README file.

The `differentiation.txt` contains our different design for our website. 

The `danger_log.txt` contains our danger log. 
