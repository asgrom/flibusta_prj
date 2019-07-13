class Node:

    def __init__(self, x, next=None, prev=None, idx=0):
        self.val = x
        self.next = next
        self.prev = prev
        self.idx = idx

    def __str__(self):
        return str(self.val)


class History:

    def __init__(self):
        self.first = None
        self.last = None
        self.length = 0

    def add(self, x):
        if self.first is None:
            self.last = self.first = Node(x)
        else:
            self.length = self.last.idx + 1
            if self.last.next is not None:
                self.last.next.prev = None
                self.last.next = None
            node = Node(x, prev=self.last, idx=self.last.idx + 1)
            self.last.next = node
            self.last = node

    def get_values(self):
        node = self.first
        vals = []
        while node:
            vals.append(node.val)
            node = node.next
        return vals

    def previous(self):
        if self.last.prev is not None:
            self.last = self.last.prev
            return self.last
        else:
            return None

    def next(self):
        if self.last.next is not None:
            self.last = self.last.next
            return self.last
        else:
            return None


if __name__ == '__main__':
    pass
