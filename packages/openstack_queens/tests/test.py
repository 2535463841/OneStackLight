class A:

    def foo(self):
        print('A')

class B:

    def foo(self):
        print('B')


class C(A, B):
    pass
    
    def main(self):
        super(C, B).foo()

c = C()
c.main()
