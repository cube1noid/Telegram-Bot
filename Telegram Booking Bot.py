from pymongo import MongoClient

username ='<insert username>'
password = '<insert password>'
dbname = '<insert database name>'
conn_str = f''

client= MongoClient(conn_str)
db = client['<insert database name>']
scheduler = db['<insert collection name>']

def db_avail_timings():
    avail_timings=[]
    pred = {'booking_status': ''}
    with scheduler.find(pred) as cur:
        for d in cur:
            avail_timings.append(d['timing'])
    return avail_timings


import telegram
from telegram.ext import Updater, CommandHandler

print(telegram.__version__)

TOKEN = '<insert telegram bot token>'
bot = telegram.Bot(TOKEN)

print(bot.get_me())
updater = Updater(TOKEN, use_context=True)


def start_func(update, context):
    user_id = update.message.from_user.id
    rows = scheduler.find_one({'user_id':user_id})
    if rows is not None:    
        if rows['user_id'] == user_id:
            update.message.reply_text(f"Hi {rows['stu_name']}, {rows['stu_id']}!! You have an existing appointment placed for {rows['timing']}. If you want to cancel your earlier reservation, type /cancel")        
    else:
        avail_timings = db_avail_timings()
        update.message.reply_text("Hi!! :D I'll help you with your booking. These are the available timings: " '\n' +'\n'.join(avail_timings))
        update.message.reply_text("To begin with your booking, please type:" '\n' + "/book<space>Name<space>Student_ID<space>Timing" '\n' + "(e.g. /book Aaron 12345X Monday9am).")

start_cmd = CommandHandler('start', start_func)
updater.dispatcher.add_handler(start_cmd)


def book_func(update, context):
    user_id = update.message.from_user.id
    s = update.message.text
    l = len(s.split()) 
    if l != 4:
        update.message.reply_text('Please book using this format:''\n' + '/book<space>Name<space>Student_ID<space>Timing''\n' + '(e.g. /book Aaron 12345X Monday9am).''\n'+ 'You may type /start to view the list of available timings.')
        return
    timeslot = s.replace('/book ', '')
    stu_name, stu_id, timing = timeslot.split()

    rows = scheduler.find({'booking_status':'booked'})
    for r in rows:
        if r['user_id'] == user_id:
            existing_timing = r['timing']
            existing_stu_name = r['stu_name']
            existing_stu_id = r['stu_id']
            update.message.reply_text(f'Hi there, you have an existing booking for {existing_timing} under the name {existing_stu_name}, {existing_stu_id}. You may type /cancel to cancel your earlier reservation to make a rebooking.')
            return

    rows = scheduler.find({'booking_status':''})
    for r in rows:
        if r['timing'] == timing:
            result = scheduler.update_one({'$and':[{'timing': timing},{'booking_status': {'$eq':""}}]}, {'$set': {'user_id':user_id,'stu_name':stu_name,'stu_id':stu_id,'booking_status':'booked'}})
            print('Matched =', result.matched_count)
            print('Modified =', result.modified_count)
            if result.modified_count == 1:
                update.message.reply_text(f'Hi {stu_name}, you have successfully booked {timing} \U0001F60A')
            else:
                update.message.reply_text(f'Hi {stu_name}, your booking is unsuccessful')
            return
    update.message.reply_text('Please input one of the available timings. You may view the available timings by typing /start')

book_cmd = CommandHandler('book', book_func)
updater.dispatcher.add_handler(book_cmd)


def cancel_func(update, context):
    user_id = update.message.from_user.id
    rows = scheduler.find_one({'user_id':user_id})
    if rows is not None:    
        canc_name = rows['stu_name']
        canc_timing = rows['timing']
        result = scheduler.update_one({'user_id': user_id}, {'$set': {'user_id':'','stu_name':'','stu_id':'', 'booking_status':''}})
        print('Matched =', result.matched_count)
        print('Modified =', result.modified_count)
        if result.modified_count == 1:
            update.message.reply_text(f'Dear {canc_name}, your booking for {canc_timing} has been successfully cancelled. You may begin the process of rebooking by typing /start')
    else:
        update.message.reply_text(f'Hi there, you have not made any bookings. You can start the process by typing /start')

cancel_cmd = CommandHandler('cancel', cancel_func)
updater.dispatcher.add_handler(cancel_cmd)


print('Start backend...')
updater.start_polling()
updater.idle()


'''
Test cases:

If no existing bookings:
/start =>  lists out available timings and how to make a booking
/book Aaron 12345X Monday9am => respond that booking is successful 
/cancel => notifies that there is no existing booking

If existing bookings:
/start => returns the details of the existing booking
/book Aaron 12345X Monday9am => returns the details of the existing booking, cannot book multiple timeslots
/cancel => replies that the booking has been successfully cancelled

Bookings with incorrect variable inputs:
/book => explains how to make a booking
/book Aaron 12345X Mon9am => refers user back to available timings

Booking with unavailable timing:
/book Aaron 12345X Sunday9am => refers user back to available timings
'''