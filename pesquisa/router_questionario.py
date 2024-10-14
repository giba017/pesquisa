from ast import Dict
from http import HTTPStatus
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from pesquisa.database import get_session
from pesquisa.models import (
    Opcao,
    Questao,
    Questionario,
    RespostaQuestao,
    RespostaQuestionario,
    TipoQuestao,
    User,
)
from pesquisa.schemas import QuestionarioSchema
from pesquisa.security import get_current_active_user

templates = Jinja2Templates(directory='pesquisa/templates')

router = APIRouter(prefix='/pesquisa', tags=['pesquisa'])
T_Session = Annotated[Session, Depends(get_session)]
T_CurrentUser = Annotated[User, Depends(get_current_active_user)]


@router.get("/questionarios/", response_class=HTMLResponse)
async def form_get_questionario(request: Request):
    return templates.TemplateResponse(
        "formQuestionario.html", {"request": request}
    )


@router.post("/questionarios/")
def criar_questionario(  # noqa: PLR0913, PLR0917
    session: T_Session,
    titulo: str = Form(...),
    descricao: str = Form(...),
    perguntas: List[str] = Form(...),
    tipos: List[str] = Form(...),
    opcoes: List[Optional[str]] = Form(...),
    limite_respostas: List[Optional[int]] | None = None,
):
    questionario = Questionario(
        titulo=titulo,
        descricao=descricao,
        questoes=[]
    )
    session.add(questionario)
    session.flush()
    session.refresh(questionario)
    for index, valor in enumerate(tipos):
        questao = None
        if valor == 'texto':
            questao = Questao(
                texto=perguntas[index],
                tipo=TipoQuestao.TEXT,
                questionario_id=questionario.id,
                limite_respostas=None,
                opcoes=None
            )
            session.add(questao)
            session.flush()
            session.refresh(questao)
        elif valor == 'select_single':
            questao = Questao(
                texto=perguntas[index],
                tipo=TipoQuestao.TEXT,
                questionario_id=questionario.id,
                limite_respostas=(int(limite_respostas) if limite_respostas else None),  # type: ignore E501
                opcoes=None
            )

            for i, v in enumerate(opcoes[index:]):
                if not opcoes[i]:
                    break
                db_opcoes = Opcao(
                    texto=str(opcoes[i]),
                    questao_id=questao.id,
                    questao=questao
                )
                session.add(db_opcoes)
                session.flush()
                session.refresh(db_opcoes)

    session.commit()
    session.refresh(questionario)
    return questionario


# Endpoint para adicionar uma questão a um questionário
@router.post("/questionarios/{questionario_id}/questoes/")
def adicionar_questao(
    session: T_Session,
    questionario_id: int,
    texto: str,
    tipo: TipoQuestao,
    opcoes: list[str] = None,
):
    questionario = session.query(Questionario).filter(
        Questionario.id == questionario_id).first()
    if not questionario:
        raise HTTPException(
            status_code=404,
            detail="Questionário não encontrado")

    questao = Questao(texto=texto, tipo=tipo, questionario_id=questionario_id)

    session.add(questao)
    session.commit()
    session.refresh(questao)

    # Se a questão for do tipo SELECT, adicionar opções
    if tipo in [TipoQuestao.SELECT_SINGLE, TipoQuestao.SELECT_MULTIPLE] and opcoes:  # noqa: E501, PLR6201
        for opcao_texto in opcoes:
            opcao = Opcao(texto=opcao_texto, questao_id=questao.id)
            session.add(opcao)
        session.commit()

    return questao


@router.post("/questionarios/{questionario_id}/respostas/")
def responder_questionario(
    questionario_id: int,
    nome: str,
    email: str,
    respostas: dict[int, list[str]],
    session: T_Session
):
    """
    Recebe as respostas de um questionário.
    - `respostas`: dicionário onde a chave é o ID da questão e o valor é:
        - para questões de texto: uma string com a resposta;
        - para questões de seleção: uma lista de IDs das opções selecionadas.
    """
    questionario = session.query(Questionario).filter(
        Questionario.id == questionario_id
    ).first()
    if not questionario:
        raise HTTPException(
            status_code=404,
            detail="Questionário não encontrado"
        )

    # Criar a resposta do questionário
    resposta_questionario = RespostaQuestionario(
        nome=nome, email=email, questionario_id=questionario_id
    )
    session.add(resposta_questionario)
    session.commit()
    session.refresh(resposta_questionario)

    # Percorrer as respostas e associá-las às questões
    for questao_id, resposta in respostas.items():
        questao = session.query(Questao).filter(
            Questao.id == questao_id, Questao.questionario_id == questionario_id
        ).first()
        if not questao:
            raise HTTPException(
                status_code=404, detail=f"Questão {questao_id} não encontrada"
            )

        # Questão do tipo texto
        if questao.tipo == TipoQuestao.TEXT:
            resposta_questao = RespostaQuestao(
                resposta_texto=resposta[0],
                questao_id=questao_id,
                resposta_questionario_id=resposta_questionario.id
            )

        # Questão de seleção única
        elif questao.tipo == TipoQuestao.SELECT_SINGLE:
            opcao = session.query(Opcao).filter(
                Opcao.id == int(resposta[0]),
                Opcao.questao_id == questao_id
            ).first()
            if not opcao:
                raise HTTPException(
                    status_code=404,
                    detail=f"Opção {resposta[0]} não encontrada\
                         para a questão {questao_id}"
                )
            resposta_questao = RespostaQuestao(
                opcao_id=opcao.id,
                questao_id=questao_id,
                resposta_questionario_id=resposta_questionario.id
            )

        # Questão de seleção múltipla com limite de respostas
        elif questao.tipo == TipoQuestao.SELECT_MULTIPLE:
            if len(resposta) > (questao.limite_respostas or len(resposta)):
                raise HTTPException(
                    status_code=400,
                    detail=f"Você só pode selecionar até\
                         {questao.limite_respostas} opções para a\
                             questão {questao_id}"
                )

            # Validar cada opção
            for opcao_id in resposta:
                opcao = session.query(Opcao).filter(
                    Opcao.id == int(opcao_id),
                    Opcao.questao_id == questao_id
                ).first()
                if not opcao:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Opção {opcao_id} não encontrada para a\
                             questão {questao_id}"
                    )
                resposta_questao = RespostaQuestao(
                    opcao_id=opcao.id,
                    questao_id=questao_id,
                    resposta_questionario_id=resposta_questionario.id
                )
                session.add(resposta_questao)

    session.commit()
    return {"message": "Respostas enviadas com sucesso!"}
