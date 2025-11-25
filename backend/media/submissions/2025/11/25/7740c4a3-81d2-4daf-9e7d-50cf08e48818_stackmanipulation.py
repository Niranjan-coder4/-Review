mappings = [
	["exch", lambda x: exch_operation(x)],
	["pop", lambda x: pop_operation(x)],
	["copy", lambda x: copy_operation(x)],
	["dup", lambda x: dup_operation(x)],
	["clear", lambda x: clear_operation(x)],
	["count", lambda x: count_operation(x)],
]

def exch_operation(stack):
	if stack.size() < 2:
		print("not enough operands.")
		return

	op1 = stack.pop()
	op2 = stack.pop()

	stack.push(op1)
	stack.push(op2)

def pop_operation(stack):
	if stack.size() < 1:
		print("not enough operands.")
		return

	stack.pop()

def copy_operation(stack):
	if stack.size() < 1:
		print("not enough operands.")
		return

	num_to_copy = stack.pop()

	if stack.size() < num_to_copy:
		print("not enough operands.")
		return

	items = []
	for _ in range(num_to_copy):
		items.append(stack.pop())

	for i in range(2):
		for item in reversed(items):
			stack.push(item)
		

def dup_operation(stack):
	if stack.size() < 1:
		print("not enough operands.")
		return

	op = stack.pop()

	stack.push(op)
	stack.push(op)

def clear_operation(stack):
	try:
		while True:
			stack.pop()
	except IndexError:
		return
	
def count_operation(stack):
	count = 0

	try:
		while True:
			stack.pop()
			count += 1
	except IndexError:
		stack.push(count)
