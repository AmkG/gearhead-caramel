from pbge.plots import Plot
import game
import gears
import pbge
import pygame
import random
from game import teams,ghdialogue
from game.content import gharchitecture,ghterrain,ghwaypoints,plotutility
from pbge.dialogue import Offer, ContextTag, Reply
from game.ghdialogue import context
from game.content.ghcutscene import SimpleMonologueDisplay
from game.content import adventureseed
from . import missionbuilder

DDBAMO_DUEL_LANCEMATE = "DDBAMO_DuelLancemate"      # Custom Element: LMNPC
DDBAMO_INVESTIGATE_METEOR = "DDBAMO_InvestigateMeteor"

class DDBAMO_PracticeDuel( Plot ):
    LABEL = DDBAMO_DUEL_LANCEMATE
    active = True
    scope = "LOCALE"
    def custom_init( self, nart ):
        myscene = self.elements["LOCALE"]
        myscene.attributes.add(gears.tags.SCENE_SOLO)
        self.register_element("ROOM",pbge.randmaps.rooms.FuzzyRoom(15,15,anchor=pbge.randmaps.anchors.middle),dident="LOCALE")

        team2 = self.register_element("_eteam",teams.Team(enemies=(myscene.player_team,)),dident="ROOM")

        mynpc = self.elements["LMNPC"]
        self.locked_elements.add("LMNPC")
        self.party_member = mynpc in nart.camp.party
        if self.party_member:
            plotutility.AutoLeaver(mynpc)(nart.camp)
        plotutility.CharacterMover(self,mynpc,myscene,team2,allow_death=False)

        self.obj = adventureseed.MissionObjective("Defeat {}".format(mynpc), missionbuilder.MAIN_OBJECTIVE_VALUE * 2)
        self.adv.objectives.append(self.obj)

        self.intro_ready = True

        return True

    def _eteam_ACTIVATETEAM(self,camp):
        if self.intro_ready:
            npc = self.elements["LMNPC"]
            ghdialogue.start_conversation(camp,camp.pc,npc,cue=ghdialogue.ATTACK_STARTER)
            self.intro_ready = False

    def LMNPC_offers(self,camp):
        mylist = list()
        mylist.append(Offer("[CHALLENGE]",
            context=ContextTag([context.CHALLENGE,])))
        return mylist

    def t_ENDCOMBAT(self,camp):
        myteam = self.elements["_eteam"]
        if len(myteam.get_active_members(camp)) < 1:
            self.obj.win(camp,100)
        if self.party_member:
            plotutility.AutoJoiner(self.elements["LMNPC"])(camp)
        #for pc in camp.party:
        #    pc.restore_all()


class DDBAMO_HelpFromTheStars( Plot ):
    LABEL = DDBAMO_INVESTIGATE_METEOR
    active = True
    scope = "LOCALE"
    UNIQUE = True
    def custom_init( self, nart ):
        myscene = self.elements["LOCALE"]
        myroom = self.register_element("ROOM",pbge.randmaps.rooms.FuzzyRoom(10,10),dident="LOCALE")
        team2 = self.register_element("_eteam",teams.Team(enemies=(myscene.player_team,)),dident="ROOM")
        team3 = self.register_element("_ateam",teams.Team(enemies=(team2,),allies=(myscene.player_team,)),dident="ROOM")
        myunit = gears.selector.RandomMechaUnit(self.rank,200,self.elements.get("ENEMY_FACTION"),myscene.environment,add_commander=False)
        team2.contents += myunit.mecha_list

        mynpc = self.register_element("NPC",gears.selector.random_character(rank=self.rank+10,job=gears.jobs.ALL_JOBS["Knight"],faction=gears.factions.TheSilverKnights,combatant=True))
        mek = plotutility.AutoJoiner.get_mecha_for_character(mynpc,True)
        mek.load_pilot(mynpc)
        self.register_element("SURVIVOR",mek,dident="_ateam")

        self.obj = adventureseed.MissionObjective("Investigate the meteor", missionbuilder.MAIN_OBJECTIVE_VALUE * 2, can_reset=False)
        self.adv.objectives.append(self.obj)
        self.intro_ready = True
        self.eteam_activated = False
        self.eteam_defeated = False
        self.pilot_left = False

        return True

    def _eteam_ACTIVATETEAM(self,camp):
        if self.intro_ready:
            npc = self.elements["NPC"]
            pbge.alert("As you approach the supposed crash site, the true nature of the falling star becomes clear: it's a lone mecha, having descended to Earth with an atmospheric drop chute. And from the look of things {}'s going to need your help.".format(npc.gender.subject_pronoun))
            self.eteam_activated = True
            if not self.pilot_left:
                ghdialogue.start_conversation(camp,camp.pc,npc,cue=ghdialogue.HELLO_STARTER)
                camp.fight.active.append(self.elements["SURVIVOR"])
            self.intro_ready = False
    def NPC_offers(self,camp):
        mylist = list()
        if self.eteam_defeated:
            mylist.append(Offer("[THANKS_FOR_MECHA_COMBAT_HELP] It would be a pleasure to fight at your side again someday.",dead_end=True,context=ContextTag([ghdialogue.context.HELLO,]),
                                effect=self.pilot_leaves_combat))
        else:
            myoffer = Offer(
                "[HELP_ME_VS_MECHA_COMBAT] I've been tracking weapons smugglers in the L5 region, and have traced their wares to {}.".format(self.elements["ENEMY_FACTION"]),
                dead_end=True, context=ContextTag([ghdialogue.context.HELLO,]))
            mylist.append(myoffer)
        return mylist
    def pilot_leaves_combat(self,camp):
        npc = self.elements["NPC"]
        npc.relationship.reaction_mod += 10
        npc.relationship.tags.add(gears.relationships.RT_LANCEMATE)
        mek = self.elements["SURVIVOR"]
        camp.scene.contents.remove(mek)
        mek.free_pilots()
        npc.place(self.elements["METROSCENE"])

        self.pilot_left = True
    def t_ENDCOMBAT(self,camp):
        if self.eteam_activated and not self.pilot_left:
            myteam = self.elements["_ateam"]
            eteam = self.elements["_eteam"]
            if len(myteam.get_active_members(camp)) < 1:
                self.obj.failed = True
            elif len(myteam.get_active_members(camp)) > 0 and len(eteam.get_active_members(camp)) < 1:
                self.eteam_defeated = True
                self.obj.win(camp, 100 - self.elements["SURVIVOR"].get_percent_damage_over_health())
                npc = self.elements["NPC"]
                ghdialogue.start_conversation(camp,camp.pc,npc,cue=ghdialogue.HELLO_STARTER)


class DDBAMO_CargoFromTheStars( Plot ):
    LABEL = DDBAMO_INVESTIGATE_METEOR
    active = True
    scope = "LOCALE"
    def custom_init( self, nart ):
        myscene = self.elements["LOCALE"]
        myroom = self.register_element("ROOM",pbge.randmaps.rooms.FuzzyRoom(10,10),dident="LOCALE")
        myfac = self.elements.get("ENEMY_FACTION")
        team2 = self.register_element("_eteam",teams.Team(enemies=(myscene.player_team,)),dident="ROOM")

        mynpc = self.seek_element(nart,"_commander",self._npc_is_good,must_find=False,lock=True)
        if mynpc:
            plotutility.CharacterMover(self,mynpc,myscene,team2)
            myunit = gears.selector.RandomMechaUnit(self.rank, 120, myfac, myscene.environment, add_commander=False)
        else:
            myunit = gears.selector.RandomMechaUnit(self.rank, 150, myfac, myscene.environment, add_commander=True)
            self.register_element("_commander",myunit.commander)

        team2.contents += myunit.mecha_list

        team3 = self.register_element("_cargoteam",teams.Team(),dident="ROOM")
        team3.contents += game.content.plotutility.CargoContainer.generate_cargo_fleet(self.rank)
        # Oh yeah, when using PyCharm, why not use ludicrously long variable names?
        self.starting_number_of_containers = len(team3.contents)

        self.obj = adventureseed.MissionObjective("Investigate the meteor", missionbuilder.MAIN_OBJECTIVE_VALUE * 2 )
        self.adv.objectives.append(self.obj)
        self.combat_entered = False
        self.combat_finished = False

        return True

    def _npc_is_good(self,nart,candidate):
        return isinstance(candidate,gears.base.Character) and candidate.combatant and candidate.faction == self.elements["ENEMY_FACTION"] and candidate not in nart.camp.party

    def _eteam_ACTIVATETEAM(self,camp):
        if not self.combat_entered:
            pbge.alert("As you approach the supposed crash site, it becomes clear what the meteor actually was: a cargo pod dropped from low orbit. It also becomes clear who the cargo belongs to...")
            npc = self.elements["_commander"]
            ghdialogue.start_conversation(camp,camp.pc,npc,cue=ghdialogue.ATTACK_STARTER)
            self.combat_entered = True

    def _commander_offers(self,camp):
        mylist = list()
        mylist.append(Offer("[WHATAREYOUDOINGHERE] This cargo is ours.",
            context=ContextTag([context.ATTACK,])))
        mylist.append(Offer("[CHALLENGE]",
            context=ContextTag([context.CHALLENGE,])))
        return mylist

    def t_ENDCOMBAT(self,camp):
        myteam = self.elements["_eteam"]
        cargoteam = self.elements["_cargoteam"]
        if len(cargoteam.get_active_members(camp)) < 1:
            self.obj.failed = True
        elif len(myteam.get_active_members(camp)) < 1:
            self.obj.win(camp,(sum([(100-c.get_percent_damage_over_health()) for c in cargoteam.get_active_members(camp)]))//self.starting_number_of_containers )
            if not self.combat_finished:
                pbge.alert("You have captured the cargo.")
                self.combat_finished = True

