import re

from stack import Stack

operand_stack = Stack()
dictionary_stack = Stack()
dictionary_stack.push({})

import arithmetic
import stackmanipulation
import strings
import dictionaries
import comparisons
import flowcontrol
import inputoutput

def process_boolean(value):
	if value == "true":
		return (True, True)
	elif value == "false":
		return (True, False)
	else:
		return False

def process_number(value):
	try:
		float_value = float(value)
		if float_value.is_integer():
			return (True, int(float_value))
		else:
			return (True, float_value)
	except ValueError:
		return False

def process_string(value):
	if value.startswith("(") and value.endswith(")"):
		return (True, value[1:-1])
	else:
		return False

def process_code_block(value):
	if len(value) >= 2 and value.startswith("{") and value.endswith("}"):
		return (True, value[1:-1].strip().split())

def process_name_constant(value):
	if value.startswith("/"):
		return (True, value)

def process_constants(input):
	res = process_boolean(input)
	res = res or process_number(input)
	res = res or process_string(input)
	res = res or process_code_block(input)
	res = res or process_name_constant(input)
	return res

def process_input(input):
	result = process_constants(input)
	if result:
		operand_stack.push(result[1])
	else:
		lookup_in_dictionary(input)

def lookup_in_dictionary(input):
	items = []

	try:
		while True:
			top_dict = dictionary_stack.peek()
			if input in top_dict:
				value = top_dict[input]
				if callable(value):
					value()
				elif isinstance(value, list):
					for item in value:
						process_input(item)
				else:
					operand_stack.push(value)
			else:
				items.append(dictionary_stack.pop())
	except KeyError:
		pass

	for item in reversed(items):
		dictionary_stack.push(item)

def repl():
	while user_input := input("REPL> "):
		if user_input.lower() == 'quit':
			break

		if isinstance(user_input.split(), list):
			pattern = r'\s+(?![^{}]*\}|[^()]*\))'
			for item in re.split(pattern, user_input):
				process_input(item)
		else:
			process_input(user_input)

		print(f"Operand Stack: {operand_stack}")

for name, proc in stackmanipulation.mappings:
	dictionary_stack.peek()[name] = lambda proc=proc: proc(operand_stack) 

for name, proc in arithmetic.mappings:
	dictionary_stack.peek()[name] = lambda proc=proc: proc(operand_stack)

for name, proc in dictionaries.mappings:
	dictionary_stack.peek()[name] = lambda proc=proc: proc(operand_stack, dictionary_stack)

for name, proc in strings.mappings:
	dictionary_stack.peek()[name] = lambda proc=proc: proc(operand_stack)

for name, proc in comparisons.mappings:
	dictionary_stack.peek()[name] = lambda proc=proc: proc(operand_stack)

for name, proc in flowcontrol.mappings:
	dictionary_stack.peek()[name] = lambda proc=proc: proc(operand_stack, process_input)

for name, proc in inputoutput.mappings:
	dictionary_stack.peek()[name] = lambda proc=proc: proc(operand_stack)

repl()
