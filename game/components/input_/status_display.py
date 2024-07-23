from typing import Generic

from game.components.input_.input_ import (
    Input,
    InputDataTypeVar,
    InputNameVar,
    ParticipantVar,
)
from game.components.send import Address
from smart_text import TextLike

class Status_Display(Generic[InputDataTypeVar,InputNameVar,ParticipantVar]):
    def __init__(self,address:Address|None = None) -> None:
        self.address = address
        self.__last_test:TextLike|None = None
        self.show_input_completion_status:bool = True
        self.hide_completed:bool = True
        self.show_participant_completion_status:bool = True
        self.show_participant_feedback:bool = True
    def identify_input(self,inpt:Input[InputDataTypeVar,InputNameVar,ParticipantVar]) -> TextLike:
        return inpt.identifier if inpt.identifier is not None else 'the input'
    def make_completion_status_text(self,inpt:Input[InputDataTypeVar,InputNameVar,ParticipantVar]) -> TextLike:
        to_return:TextLike = ''
        is_done = inpt.is_done()
        if is_done and self.hide_completed:
            return to_return
        to_return += (
            self.identify_input(inpt) + 
            (' has been completed' if is_done else
            ' is not yet completed')
        )
        to_return += '.\n'
        to_return = to_return.capitalize()
        return to_return
    def make_participant_status(self,inpt:Input[InputDataTypeVar,InputNameVar,ParticipantVar],participant:ParticipantVar):
        to_return:TextLike = ''
        value:InputDataTypeVar|None = inpt.responses[participant]
        valid:bool
        feedback:TextLike|None
        valid,feedback = inpt.response_validator(participant,value)
        show_completed = self.show_input_completion_status and not (valid and self.hide_completed)
        if show_completed:
            to_return += (
                ' has ' + ('' if valid else 'not ') +
                'submitted a valid response to ' +
                self.identify_input(inpt)
            )
        if self.show_participant_feedback and feedback is not None:
            if show_completed:
                to_return += ' and'
            to_return += (
                ' has received the feedback ' +
                feedback
            )
        if to_return == '':
            return ''
        to_return = participant.mention + ' ' + to_return + '.\n'
        return to_return
    def make_participants_status(self,inpt:Input[InputDataTypeVar,InputNameVar,ParticipantVar]):
        to_return:TextLike = ''
        for participant in inpt.participants:
            to_return += self.make_participant_status(inpt,participant)
        return to_return
    def make_text(self,inpt:Input[InputDataTypeVar,InputNameVar,ParticipantVar]) -> TextLike:
        to_return:TextLike = ""
        to_return += self.make_completion_status_text(inpt)
        to_return += self.make_participants_status(inpt)
        return to_return
    async def __call__(self,inpt:Input[InputDataTypeVar,InputNameVar,ParticipantVar]):
        new_text = self.make_text(inpt)
        if new_text == self.__last_test:
            return
        self.__last_test = new_text
        self.address = await inpt.send(address=self.address,text=new_text)