#import esp
#esp.osdebug(None)
import gc
gc.collect()

exec(open('main.py').read())
