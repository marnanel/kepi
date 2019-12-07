from django.dispatch import Signal

created = Signal(
        providing_args=[
            'value',
            ])

updated = Signal(
        providing_args=[
            'value',
            ])

deleted = Signal(
        providing_args=[
            'url',
            'entombed',
            ])
