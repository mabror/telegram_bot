from django.core.management.base import BaseCommand
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from bot.models import Product, User
from project.validators import PhoneValidator
from django.conf import settings


class Command(BaseCommand):
    PAGE_LIMIT = 3

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self.updater = Updater("1900837405:AAGSxRVaLW862xflLBRFODz_Xjs3czq-b0w")

    def find_user(self, update: Update):
        return User.objects.get(telegram_user_id=update.message.from_user.id)

    def registration(self, update, first_name, last_name, phone_number):
        first_name = first_name or ""
        last_name = last_name or ""
        try:
            user = self.find_user(update)
        except User.DoesNotExist:
            try:
                user = User.objects.get(phone=phone_number)
            except User.DoesNotExist:
                user = User(phone=phone_number)

        user.username = "tg{}".format(update.message.from_user.id)
        user.first_name = first_name
        user.last_name = last_name
        user.telegram_user_id = update.message.from_user.id
        user.save()

        update.message.reply_text("Welcome to bot pls click /products",
                                  reply_markup=ReplyKeyboardRemove())

    def command_start(self, update: Update, context: CallbackContext):
        try:
            user = self.find_user(update)
            self.updater.bot.send_message(chat_id=update.message.chat_id, text="Welcome to bot pls click /products")

        except User.DoesNotExist:
            user = User()
            self.updater.bot.send_message(chat_id=update.message.chat_id,
                                          text="Welcome please take phone number or click button to regist",
                                          reply_markup=ReplyKeyboardMarkup(keyboard=[
                                              [KeyboardButton(request_contact=True, text="Send mobile number"), "ok"],

                                          ]))

    def generate_inline_data(self, user, all_page):
        offset = user.current_page * self.PAGE_LIMIT
        buttons = []
        for row in Product.objects.order_by("-id")[offset:offset + self.PAGE_LIMIT]:
            buttons.append([InlineKeyboardButton(text=row.button_title, callback_data="p{}".format(row.id))])

        last_line = []
        if user.current_page > 0:
            last_line.append(InlineKeyboardButton(text="«", callback_data="dec"))

        if user.current_page + 1 < all_page:
            last_line.append(InlineKeyboardButton(text="»", callback_data="inc"))

        buttons.append(last_line)
        return {
            'text': "Page: {}/{}".format(user.current_page + 1, all_page),
            'reply_markup': InlineKeyboardMarkup(buttons)
        }

    def contact_handler(self, update: Update, context):
        contact = update.message.contact
        self.registration(update, contact.first_name, contact.last_name, contact.phone_number)

    def message_handler(self, update: Update, context: CallbackContext):
        phone = PhoneValidator.clean(update.message.text)
        if not PhoneValidator.validate(phone):
            update.message.reply_text("Mobile number wrong", reply_to_message_id=update.message.message_id)
            return
        # print(phone)
        # update.message.reply_text("Nima gap?", reply_to_message_id=update.message.message_id)

        self.registration(update, update.message.from_user.first_name, update.message.from_user.last_name, phone)

    def command_products(self, update: Update, context):
        try:
            user = self.find_user(update)
        except:
            update.message.reply_text("pls clikc /start")
            return

        all_page = (Product.objects.count() // self.PAGE_LIMIT) + 1
        data = self.generate_inline_data(user, all_page)

        self.updater.bot.send_message(chat_id=update.message.chat_id, **data)

    def page_inline_handler(self, update: Update, context):
        try:
            user = User.objects.get(telegram_user_id=update.callback_query.from_user.id)
            # raise Exception('123')
        except:
            update.callback_query.answer("pls clikc /start")
            return

        if update.callback_query.data == "inc":
            user.current_page += 1
        else:
            user.current_page -= 1

        all_page = (Product.objects.count() // self.PAGE_LIMIT) + 1

        user.current_page = min(max(user.current_page, 0), all_page)
        user.save()

        data = self.generate_inline_data(user, all_page)

        update.callback_query.edit_message_text(**data)

    def products_handler(self, update: Update, context):
        id = int(update.callback_query.data[1:])
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            update.callback_query.answer("Product not found")
            return

        print(settings.MEDIA_ROOT / str(product.image))
        update.callback_query.answer()
        self.updater.bot.send_photo(chat_id=update.callback_query.message.chat_id,
                                    photo=open(settings.MEDIA_ROOT / str(product.image), "rb"),
                                    caption="* {} * \n\n{}".format(product.subject, product.content),
                                    parse_mode="markdown")
        # self.updater.bot.send_message(chat_id=update.callback_query.message.chat_id,
        #                               text="* {} * \n\n{}".format(product.subject, product.content),
        #                               parse_mode="markdown")

    def handle(self, *args, **options):
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(CommandHandler("start", self.command_start))
        dispatcher.add_handler(CommandHandler("products", self.command_products))
        dispatcher.add_handler(CallbackQueryHandler(self.page_inline_handler, pattern="^(dec|inc)$"))
        dispatcher.add_handler(CallbackQueryHandler(self.products_handler, pattern="^p[0-9]+$"))

        dispatcher.add_handler(MessageHandler(Filters.contact, self.contact_handler))
        dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, self.message_handler))

        self.updater.start_polling()
        self.updater.idle()
