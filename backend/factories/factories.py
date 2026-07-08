from datetime import date

import factory
from factory.alchemy import SQLAlchemyModelFactory

from backend.factories.helpers import (
    DIMENSIONI_VALIDHE,
    FREQUENZE_VALIDHE,
    data_ultimo_intervento_per_stato,
)
from backend.factories.session import get_factory_session, register_factory
from backend.models import Filtro, Intervento, Linea, QuadroElettrico, Reparto, Sede


class _BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "flush"


@register_factory
class SedeFactory(_BaseFactory):
    class Meta:
        model = Sede
        sqlalchemy_session = get_factory_session()

    sede = factory.Sequence(lambda n: f"Sede {n}")


@register_factory
class RepartoFactory(_BaseFactory):
    class Meta:
        model = Reparto
        sqlalchemy_session = get_factory_session()

    reparto = factory.Sequence(lambda n: f"Reparto {n}")
    sede = factory.SubFactory(SedeFactory)


@register_factory
class LineaFactory(_BaseFactory):
    class Meta:
        model = Linea
        sqlalchemy_session = get_factory_session()

    linea = factory.Sequence(lambda n: f"Linea {n}")
    reparto = factory.SubFactory(RepartoFactory)


@register_factory
class InterventoStatoFactory(_BaseFactory):
    class Meta:
        model = Intervento
        sqlalchemy_session = get_factory_session()

    class Params:
        stato_target = "ok"

    data = factory.LazyAttribute(
        lambda o: data_ultimo_intervento_per_stato(o.stato_target, o.filtro.frequenza_intervento)
    )
    note = factory.LazyAttribute(
        lambda o: f"Intervento di esempio — stato {o.stato_target}"
    )


@register_factory
class FiltroFactory(_BaseFactory):
    class Meta:
        model = Filtro
        sqlalchemy_session = get_factory_session()

    class Params:
        stato = None

    quantita_filtri = factory.Sequence(lambda n: (n % 12) + 1)
    dimensione_filtri = factory.Iterator(DIMENSIONI_VALIDHE)
    frequenza_intervento = factory.Iterator(FREQUENZE_VALIDHE)
    quadro_elettrico = factory.SubFactory(
        "backend.factories.factories.QuadroElettricoFactory",
        filtro=None,
    )

    intervento_per_stato = factory.Maybe(
        "stato",
        yes_declaration=factory.RelatedFactory(
            InterventoStatoFactory,
            factory_related_name="filtro",
            stato_target=factory.SelfAttribute("..stato"),
        ),
    )

    @factory.post_generation
    def _unico_per_quadro(obj, create, extracted, **kwargs):
        if not create:
            return
        filtri = list(obj.quadro_elettrico.filtri)
        if len(filtri) > 1:
            nome = obj.quadro_elettrico.quadro_elettrico
            raise ValueError(f"Il quadro '{nome}' può avere un solo filtro.")


@register_factory
class QuadroElettricoFactory(_BaseFactory):
    class Meta:
        model = QuadroElettrico
        sqlalchemy_session = get_factory_session()

    class Params:
        stato = None
        quantita_filtri = factory.Sequence(lambda n: (n % 12) + 1)
        dimensione_filtri = factory.Iterator(DIMENSIONI_VALIDHE)
        frequenza_intervento = factory.Iterator(FREQUENZE_VALIDHE)

    quadro_elettrico = factory.Sequence(lambda n: f"Quadro {n}")
    linea = factory.SubFactory(LineaFactory)

    filtro = factory.RelatedFactory(
        FiltroFactory,
        factory_related_name="quadro_elettrico",
        stato=factory.SelfAttribute("..stato"),
        quantita_filtri=factory.SelfAttribute("..quantita_filtri"),
        dimensione_filtri=factory.SelfAttribute("..dimensione_filtri"),
        frequenza_intervento=factory.SelfAttribute("..frequenza_intervento"),
    )


@register_factory
class InterventoFactory(_BaseFactory):
    class Meta:
        model = Intervento
        sqlalchemy_session = get_factory_session()

    data = factory.LazyFunction(date.today)
    note = factory.Faker("sentence", locale="it_IT")
    filtro = factory.SubFactory(FiltroFactory)
