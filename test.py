from opendocument import ODFDocument

doc_path = 'test.odt'
template_path = 'styles.ott'

doc = ODFDocument(doc_path, template_path, overwrite=True)

doc.add_heading("The title", 1)
with doc.paragraph():
    doc.add_text("Some text. ", 'Normal')
    doc.add_text("This is bold. ", 'Bold')

with doc.list():
    with doc.list_item():
        with doc.paragraph(style='Bullet'):
            doc.add_text("Item 1.")
    with doc.list_item():
        with doc.paragraph(style='Bullet'):
            doc.add_text("Item 2.")
        with doc.list():
            with doc.list_item():
                with doc.paragraph(style='Bullet within bullet'):
                    doc.add_text("Item 2.1. This is ")
                    doc.add_text("code", "Code In Text")
                    doc.add_text(". Oh, and here is a link: ")
                    doc.add_text("http://google.com", 'URL')
                    doc.add_text(".")
    with doc.list_item():
        with doc.paragraph(style='Bullet'):
            doc.add_text("Item 3.")
with doc.paragraph():
    doc.add_text("Some text. ", 'Normal')
with doc.paragraph('Code'):
    doc.add_text("print('Hello world!')")

doc.save()
