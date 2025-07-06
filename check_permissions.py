"""
Script pour vérifier les permissions d'un compte dans un canal
"""
import asyncio
from telethon import TelegramClient
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator

async def check_permissions():
    # Utiliser la session existante
    client = TelegramClient('telefeed_22967924076', 21341224, '2d910cf3998019516d6d4bfe81b9a065')
    
    await client.start()
    
    # ID du canal de destination
    channel_id = -4922594370
    
    try:
        # Obtenir l'entité du canal
        channel = await client.get_entity(channel_id)
        print(f"Canal : {channel.title}")
        print(f"Type : {'Canal' if channel.broadcast else 'Groupe'}")
        
        # Vérifier les permissions de l'utilisateur actuel
        me = await client.get_me()
        print(f"Compte connecté : {me.first_name} ({me.id})")
        
        # Obtenir les permissions
        permissions = await client.get_permissions(channel)
        print(f"\nPermissions dans le canal :")
        print(f"- Publier des messages : {permissions.post_messages}")
        print(f"- Modifier les messages : {permissions.edit_messages}")  
        print(f"- Supprimer les messages : {permissions.delete_messages}")
        print(f"- Administrateur : {permissions.is_admin}")
        
        # Essayer d'envoyer un message de test
        test_message = await client.send_message(channel, "🔧 Test de permissions - Message envoyé par TeleFeed")
        print(f"\n✅ Message de test envoyé avec succès (ID: {test_message.id})")
        
        # Attendre 2 secondes puis supprimer le message de test
        await asyncio.sleep(2)
        await client.delete_messages(channel, test_message.id)
        print("✅ Message de test supprimé")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_permissions())