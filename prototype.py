import pygame
import math
import paho.mqtt.client as mqtt
import config

# Access the constants from the config module
board_width = config.board_width
board_height = config.board_height
origin_x = config.origin_x
origin_y = config.origin_y
arm_1_length = config.arm_1_length
arm_2_length = config.arm_2_length
broker_ip = config.broker_ip
topic = config.topic
username = config.username
password = config.password


def draw_origin():
    board.fill((255, 255, 255))  # Clear the board

    # Draw the origin (initial point) on the board
    pygame.draw.circle(board, (255, 0, 0), (origin_x, origin_y), 3)
    # Draw a circle centered on the origin with a radius of arm_1_length
    pygame.draw.circle(board, (0, 0, 255), (origin_x, origin_y), arm_1_length, 1)


def get_target():
    x, y = pygame.mouse.get_pos()

    # Draw a red dot at clicked position
    pygame.draw.circle(board, (255, 0, 0), (x, y), 3)

    # Draw a circle centered on the clicked point with a radius of arm_2_length
    pygame.draw.circle(board, (0, 0, 255), (x, y), arm_2_length, 1)

    # Display the coordinates on the board near the red dot
    display_coords(x, y, x + 10, y - 10)

    return x, y


def find_intersection(x, y):
    dx = x - origin_x
    dy = y - origin_y
    d = (arm_1_length ** 2 - arm_2_length ** 2 + distance ** 2) / (2 * distance)
    h = (arm_1_length ** 2 - d ** 2) ** 0.5
    x1 = origin_x + (d * dx - h * dy) / distance
    y1 = origin_y + (h * dx + d * dy) / distance
    x2 = origin_x + (d * dx + h * dy) / distance
    y2 = origin_y + (-h * dx + d * dy) / distance

    # Draw the points of intersection
    pygame.draw.circle(board, (255, 0, 0), (int(x1), int(y1)), 3)
    pygame.draw.circle(board, (255, 0, 0), (int(x2), int(y2)), 3)

    return x1, y1, x2, y2


def draw_lines(x1, y1, x2, y2):
    # Draw lines from origin to intersection points and from there to the clicked point
    pygame.draw.line(board, (0, 0, 0), (origin_x, origin_y), (x1, y1), 1)
    pygame.draw.line(board, (0, 0, 0), (x1, y1), (x2, y2), 1)


def find_angles(x1, y1, x2, y2):
    # Calculate angles between lines
    angle_origin_to_intersect = calculate_angle(origin_x, origin_y, x1, y1)
    angle_intersect_to_target = calculate_angle(x1, y1, x2, y2)

    if angle_origin_to_intersect < angle_intersect_to_target:
        relative_angle = 90 + angle_intersect_to_target - angle_origin_to_intersect
    else:
        relative_angle = 90 + angle_intersect_to_target - angle_origin_to_intersect

    return int(angle_origin_to_intersect), int(relative_angle)


def calculate_angle(x1, y1, x2, y2):
    delta_x = x2 - x1
    delta_y = y2 - y1
    return math.degrees(math.atan2(delta_y, delta_x))


def display_angle(angle, label_x, label_y):
    # Display angles near the respective lines
    angle_surface = font.render(f"{int(angle)} deg", True, (0, 0, 0))
    angle_rect = angle_surface.get_rect()
    angle_rect.center = (label_x, label_y)
    board.blit(angle_surface, angle_rect)


def display_coords(x, y, label_x, label_y):
    # Display the coordinates on the board near the red dot
    text_surface = font.render(f"({x}, {y})", True, (0, 0, 0))
    text_rect = text_surface.get_rect()
    text_rect.topleft = (label_x, label_y)
    board.blit(text_surface, text_rect)


def select_angles(angle1, angle2):
    diff_1 = abs(angle1[0] - 90) + abs(angle2[0] - 90)
    diff_2 = abs(angle1[1] - 90) + abs(angle2[1] - 90)

    if diff_1 > diff_2:
        selected_angle_1 = angle1[0]
        selected_angle_2 = angle2[0]
        selected_intersect_x = intersect_x1
        selected_intersect_y = intersect_y1
    else:
        selected_angle_1 = angle1[1]
        selected_angle_2 = angle2[1]
        selected_intersect_x = intersect_x2
        selected_intersect_y = intersect_y2

    return selected_angle_1, selected_angle_2, selected_intersect_x, selected_intersect_y


def publish_mqtt(angle1, angle2):
    try:
        # Publish data over MQTT
        client = mqtt.Client()
        client.username_pw_set(username, password)
        client.connect(broker_ip)
        message = str(angle1) + "," + str(angle2)
        client.publish(topic, message)
        client.disconnect()
        return True
    except Exception as e:
        # Handle exceptions
        print("Error:", e)
        return False


# Initialize Pygame
pygame.init()
board = pygame.display.set_mode((board_width, board_height))
pygame.display.set_caption("Robotic Arm Simulation")
board.fill((255, 255, 255))  # Fill the board with white
font = pygame.font.Font(None, 20)

# Initialize window
draw_origin()
pygame.display.flip()

# Main loop
running = True
while running:

    # Initialize variables
    angle_1 = [0, 0]
    angle_2 = [0, 0]
    intersect_1 = [0, 0]
    intersect_2 = [0, 0]

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                draw_origin()

                # Get target point from user
                target_x, target_y = get_target()

                # Find the position of elbow
                distance = ((target_x - origin_x) ** 2 + (target_y - origin_y) ** 2) ** 0.5
                if distance <= arm_1_length + arm_2_length:

                    # Find intersections
                    intersect_x1, intersect_y1, intersect_x2, intersect_y2 = find_intersection(target_x, target_y)

                    # Display the coordinates of the points of intersection on the board
                    display_coords(int(intersect_x1), int(intersect_y1), int(intersect_x1)+10, int(intersect_y1)-10)
                    display_coords(int(intersect_x2), int(intersect_y2), int(intersect_x2)+10, int(intersect_y2)-10)

                    # Calculate angles between lines
                    angle_1[0], angle_2[0] = find_angles(intersect_x1, intersect_y1, target_x, target_y)
                    angle_1[1], angle_2[1] = find_angles(intersect_x2, intersect_y2, target_x, target_y)

                    # Select the pair of angles more distant to 90
                    final_angle_1, final_angle_2, selected_intercept_x, selected_intercept_y =\
                        select_angles(angle_1, angle_2)

                    # Draw line from origin to selected interception and to target
                    draw_lines(selected_intercept_x, selected_intercept_y, target_x, target_y)

                    # Display selected angles
                    display_angle(final_angle_1, (origin_x + selected_intercept_x) // 2,
                                  (origin_y + selected_intercept_y) // 2)
                    display_angle(final_angle_2, (selected_intercept_x + target_x) // 2,
                                  (selected_intercept_y + target_y) // 2)

                    # Print the selected pair
                    print("Angles:", final_angle_1, final_angle_2)

                    # Publish data over MQTT
                    if final_angle_1 > 0:
                        publish_mqtt(final_angle_1, final_angle_2)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
