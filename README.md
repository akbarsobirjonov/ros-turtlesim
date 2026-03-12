# ROS Turtlesim 

This project is a ROS Python program that uses the **turtlesim simulator**.

The program creates **four turtles** and controls them simultaneously.  
Each turtle draws one digit of the student ID number **0212**.

## Features

- Four turtles are created in turtlesim
- Each turtle draws one digit
- Digits are drawn simultaneously using multithreading
- Final result: **0 2 1 2** displayed from left to right

## ROS Topics Used

`/turtleX/cmd_vel`

Message type:

`geometry_msgs/Twist`

## ROS Services Used

`/spawn`  
`/teleport_absolute`  
`/set_pen`

## How to Run

Start ROS:
roscore

Start turtlesim:
rosrun turtlesim turtlesim_node

Run the program:
rosrun hw1_turtlesim hw1_U2210212.py


## Result
The turtles draw the digits **0212** simultaneously in the turtlesim window.

## Author
Akbar Sobirjonov