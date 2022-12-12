import os
import asyncio
import logging
import tornado.web
import motor.motor_asyncio
import hashlib



CONNECTION_STRING = "mongodb+srv://mvh:123@cluster-mvh-tornado1.wmcb6ko.mongodb.net/?retryWrites=true&w=majority"
client = motor.motor_asyncio.AsyncIOMotorClient(CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True)
database = client['my_database']


logging.basicConfig(filename='log/read_files.log', encoding='utf-8', level=logging.INFO)



class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")



class PUTHandler(BaseHandler):
    def initialize(self):
        self.database = database

    @tornado.web.authenticated
    async def get(self, *args):
        self.email_user = tornado.escape.xhtml_escape(self.current_user)
        user = await self.settings['database']['users'].find_one({'user': self.email_user})
        files_list = user['files_path']
        return self.render('upload_page.html', files_list=files_list, name=self.email_user)

    def prepare(self):
        self.request.connection.set_max_body_size(256*1024*1024)

    @tornado.web.authenticated
    async def post(self, filename):
        info = tornado.escape.json_decode(self.request.body)
        file_location = 'static/file/' + info['filename']
        file = open(file_location, 'x')
        file.close()
        user = tornado.escape.xhtml_escape(self.current_user)
        logging.info('"%s" created "%s"', user, file_location)
        
    @tornado.web.authenticated
    async def put(self, filename):
        chunk = self.request.body
        file_location = 'static/file/' + filename
        file_length = int(self.request.headers['Content-Range'].split('/')[1])
        with open(file_location, 'ab') as f:
            f.write(chunk)
            logging.info('"%s" received %d bytes', file_location, len(chunk))

        bytes_read = os.path.getsize(file_location)

        if bytes_read < file_length:
            self.set_status(308)
            self.set_header("Range", str(len(chunk)))
        else:
            email = tornado.escape.xhtml_escape(self.current_user)
            await self.settings['database']['users'].update_one({'user': email}, {'$push': {'files_path': file_location}})
            self.set_status(200)
            self.set_header("Range", str(len(chunk)))
            
            
class RegisterHandler(BaseHandler):
    def _initialize(self, database) -> None:
        self.database = database
        return super()._initialize()

    def md5_hash(self, password):
        database_password = password + '5gz'
        hashed = hashlib.md5(database_password.encode())
        return hashed.hexdigest()

    async def get(self):
        return self.render("register.html")

    async def post(self):
        email = self.get_body_argument('email')
        already_taken = await self.settings['database']['users'].find_one({'user': email})
        if already_taken is not None:
            error_msg = u"?error=" + tornado.escape.url_escape("Login name already taken")
            self.redirect(u"/register" + error_msg)
        hashed_pass = self.md5_hash(self.get_body_argument('password'))
        user = {}
        user['user'] = email
        user['password'] = hashed_pass
        user['files_path'] = []
        await self.settings['database']['users'].insert_one(user)
        self.redirect('/login')


class LoginHandler(BaseHandler):
    def _initialize(self, database):
        self.database = database
        return super()._initialize()

    def get(self):
        return self.render('login.html')

    def md5_hash(self, password):
        database_password = password + '5gz'
        hashed = hashlib.md5(database_password.encode())
        return hashed.hexdigest()

    async def post(self):
        username = self.get_argument('email')
        password = self.md5_hash(self.get_argument('password'))
        user = {'user': username, 'password': password}
        user = await self.settings['database']['users'].find_one(user)
        if user is not None:
            self.set_secure_cookie('user', username)
            self.redirect('/upload/')


class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect('/login')


settings = {
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    "login_url": "/login",
    "debug": True,
    "compiled_template_cache": False,
}
async def main():
    application = tornado.web.Application([
        (r"/upload/(.*)", PUTHandler),
        (r"/login", LoginHandler),
        (r'/logout', LogoutHandler),
        (r'/register', RegisterHandler),
    ], **settings,
    database=database)
    application.listen(8000)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())