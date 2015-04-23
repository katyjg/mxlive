from django.template import Library, Node, TemplateSyntaxError

register = Library()

class ContentboxNode(Node):
    
    def __init__(self, nodelist, ctx):
        self.nodelist = nodelist
        self.title = ctx['title']
        self.cls = ctx['class']
        
    def render(self, context):
        title = self.title.resolve(context)
        cls = self.cls.resolve(context)
        output = self.nodelist.render(context)
        return '''<div class="%s"><div class="title">%s</div><div class="boxcontent">%s</div></div>''' % (cls, title, output)

def do_contentbox(parser, token):
    nodelist = parser.parse(('endcontentbox',))
    parser.delete_first_token()
    try:
        title, cls = token.split_contents()[1:]
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires exactly three arguments" % \
              token.contents.split()[0]
    ctx = {'title':  parser.compile_filter(title), 'class': parser.compile_filter(cls) }
    return ContentboxNode(nodelist, ctx)


register.tag('contentbox', do_contentbox)
