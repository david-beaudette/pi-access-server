import web
from web import form

urls = (
    '/', 'index',
    '/commutator', 'commutator'
)

class index:
    def GET(self):
        return "pi-access-server index available soon."

class commutator:
    def GET(self):
        return "pi-access-server commutator functions available soon."

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
