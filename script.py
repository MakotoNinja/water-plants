#!/usr/bin/env python

'''
 ' A farmware for a custom tool for Farmbot
'''

import os, sys, json, Qualify
from random import randint
from farmware_tools import device, app, get_config_value
from Coordinate import Coordinate

def chomp():
	for i in range(NUM_BITES):
		device.log('Pass {} of {}'.format(i, NUM_BITES), 'warn')
		device.set_servo_angle(SERVO_PIN, SERVO_OPEN_ANGLE)
		coord.set_axis_position('z', BED_HEIGHT - (i * BITE_ADVANCE))
		coord.move_abs();
		device.set_servo_angle(SERVO_PIN, SERVO_CLOSE_ANGLE)
		device.wait(500)
		coord.set_axis_position('z', BED_HEIGHT + 100)
		coord.move_abs();
		coord.set_offset_axis_position(DUMP_OFFSET['axis'], DUMP_OFFSET['value'])
		coord.move_abs();
		device.set_servo_angle(SERVO_PIN, SERVO_OPEN_ANGLE)
		device.wait(250)
		coord.set_offset_axis_position(DUMP_OFFSET['axis'], 0)
		coord.move_abs();

def deploy():
	device.log('before loop...', 'warn')
	for plant in target_plants:
		device.log(json.dumps(plant))
		device.set_servo_angle(SERVO_PIN, SERVO_OPEN_ANGLE)
		device.log('set Z to translate height.', 'warn')
		coord.set_axis_position('z', Z_TRANSLATE, move_abs=True)				# move to translate height
		device.log('reset offset.', 'warn')
		coord.set_offset(0, 0, 0, move_abs=True)								# reset offset
		device.log('go to plant stage.', 'warn')
		coord.set_coordinate(PLANT_STAGE['x'], PLANT_STAGE['y'], move_abs=True)	# move above plant stage
		device.log('move down to plant.', 'warn')
		coord.set_axis_position('z', PLANT_STAGE['z'], move_abs=True)			# move down to plant stage
		device.log('pinch plant.', 'warn')
		device.set_servo_angle(SERVO_PIN, SERVO_CLOSE_ANGLE)					# bite down on plant
		device.log('move to translate height.', 'warn')
		coord.set_axis_position('z', Z_TRANSLATE, move_abs=True)				# move to translate height
		device.log('move to plant area.', 'warn')
		coord.set_coordinate(plant['x'], plant['y'], move_abs=True)				# move above current plant
		device.log('lower into hole.', 'warn')
		coord.set_axis_position('z', BED_HEIGHT - BITE_ADVANCE * NUM_BITES)		# lower into hole
		device.log('drop payload.', 'warn')
		device.set_servo_angle(SERVO_PIN, SERVO_OPEN_ANGLE)						# drop payload

PIN_LIGHTS = 7
PKG = 'Audrey II'

SERVO_PIN = Qualify.integer(PKG, 'servo_pin')
SERVO_OPEN_ANGLE = Qualify.integer(PKG, 'servo_open_angle')
SERVO_CLOSE_ANGLE = Qualify.integer(PKG, 'servo_close_angle')
PLANT_TYPE = get_config_value(PKG, 'plant_type', str).lower()
Z_TRANSLATE = Qualify.integer(PKG, 'z_translate')
BED_HEIGHT = Qualify.integer(PKG, 'bed_height')
NUM_BITES = Qualify.integer(PKG, 'num_bites')
BITE_ADVANCE = Qualify.integer(PKG, 'bite_advance')
DUMP_OFFSET = Qualify.combo(PKG, 'dump_offset')
PLANT_STAGE_ID = Qualify.integer(PKG, 'plant_stage_id')
PLANT_STAGE = Qualify.get_tool(PLANT_STAGE_ID)

audrey_retrieve_sequence_id = Qualify.sequence(PKG, 'audrey_retrieve')
audrey_return_sequence_id = Qualify.sequence(PKG, 'audrey_return')

if len(Qualify.errors):
	for err in Qualify.errors:
		device.log(err, 'error', ['toast'])
	sys.exit()
else:
	device.log('No config errors detected')

all_plants = app.get_plants()
target_plants = [];
for plant in all_plants:
	if plant['name'].lower() == PLANT_TYPE:
		target_plants.append(plant)

if not len(target_plants):
	device.log('No plants found with name: "{}"'.format(PLANT_TYPE))
	sys.exit()

device.log('Target Plants: {}'.format(json.dumps(target_plants)))
device.write_pin(PIN_LIGHTS, 1, 0)

device.execute(audrey_retrieve_sequence_id)
coord = Coordinate(device.get_current_position('x'), device.get_current_position('y'), Z_TRANSLATE)
coord.move_abs()
for site in target_plants:
	coord.set_coordinate(site['x'], site['y'], Z_TRANSLATE)
	coord.move_abs()
	chomp()
	coord.set_axis_position('z', Z_TRANSLATE)
	coord.move_abs()
device.log('Deploying...', 'warn')
deploy()
device.execute(audrey_return_sequence_id)

device.home('all')
device.write_pin(PIN_LIGHTS, 0, 0)
