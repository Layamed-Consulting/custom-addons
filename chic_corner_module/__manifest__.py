{
    'name': "CC CUSTOM",
    'description': "Chic Corner",
    'summary': "",
    'author': 'ST',
    'category': 'base',
    'version': '1.0',
    'description': """
        This module introduces custom features for the Chic Corner system, including new models, views, and logic to improve functionality.
    """,
    'author': 'LAYAMEDCONSULTING',
    'website': 'http://www.yourcompanywebsite.com',
    'category': '',
    'depends': ['base', 'sale', ],
    'data': [
        'report/bon_de_sortie_report.xml',
        'report/bon_de_sortie_template.xml',
        'report/bon_de_sortie_template_print.xml',
        'report/sale_report.xml',
        'views/report_template_vente.xml',
        'views/product_view_inherit.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'chic_corner_module/static/src/css/bon_sortie_css.css',
            'chic_corner_module/static/src/css/report_css.css',
        ],
        'web.assets_backend': [
           'chic_corner_module/static/src/models/barcode_picking.js',
        ],
        'point_of_sale._assets_pos': [
           'chic_corner_module/static/src/app/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
