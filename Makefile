    
.SUFFIXES:

clean:
	$(shell find . -type f | grep $py.class | xargs rm)
	$(shell find . -type f | grep pyc$ | xargs rm)
