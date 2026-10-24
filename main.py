import discord
from discord.ext import commands
from discord.ui import Button, View
import requests
import random
import string
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- AYARLAR -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ROBLOX_GROUP_ID = 15093066
ROBLOX_COOKIE = "BURAYA_ROBLOX_BOT_COOKIE_GELECEK"

WELCOME_CHANNEL_ID = None

pending_verifications = {} 
verified_users = {}        

DATA_FILE = "roblox_users.json"
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            verified_users = json.load(f)
    except Exception:
        verified_users = {}

def save_users():
    with open(DATA_FILE, "w") as f:
        json.dump(verified_users, f, indent=4)
# -------------------------------------------

class FormView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 İcraat Formu", style=discord.ButtonStyle.secondary, custom_id="btn_icraat_form")
    async def btn_icraat(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="📋 İCRAAT FORMU", description="Aşağıdaki şablonu kopyalayıp **İcraat Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nİcraati yapan:\nİcraati yapanın rütbesi:\nİcraati:\nKanıtlar:\n```", inline=False)
        embed.set_footer(text="Güvenlik Departmanı Resmi Botu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📁 Dosya Formu", style=discord.ButtonStyle.secondary, custom_id="btn_dosya_form")
    async def btn_dosya(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="📁 DOSYA FORMU", description="Aşağıdaki şablonu kopyalayıp **Dosya Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nDosyayla ilgilenen:\nDosyayla İlgilenin Rütbesi:\nDosyalananın İsmi:\nDosyalananın Discord İsmi:\nDosyalanma Sebebi:\nDosya Delilleri:\n```", inline=False)
        embed.set_footer(text="Güvenlik Departmanı Resmi Botu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚖️ Ceza Formu", style=discord.ButtonStyle.secondary, custom_id="btn_ceza_form")
    async def btn_ceza(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="⚖️ CEZA FORMU", description="Aşağıdaki şablonu kopyalayıp **Ceza Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nCeza neden:\nCeza veren:\nCeza alan:\nCeza alanın rütbesi:\nCeza verinin rütbesi:\nCeza:\nKanıt:\n```", inline=False)
        embed.add_field(name="📌 Not:", value="Not", inline=False)
        embed.set_footer(text="Güvenlik Departmanı Resmi Botu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class KayitModal(discord.ui.Modal, title="🔗 Roblox Hesap Bağlama"):
    roblox_username = discord.ui.TextInput(label="Roblox Kullanıcı Adınız", placeholder="Örn: Ahmet123", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        username = self.roblox_username.value.strip()
        
        req = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]})
        if req.status_code != 200 or not req.json().get("data"):
            await interaction.response.send_message(f"❌ **{username}** adında bir Roblox kullanıcısı bulunamadı!", ephemeral=True)
            return

        user_data = req.json()["data"][0]
        roblox_id = user_data["id"]

        code = "BTF-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        pending_verifications[str(interaction.user.id)] = {"roblox_name": user_data["name"], "roblox_id": roblox_id, "code": code}

        embed_dm = discord.Embed(title="🔒 Gizli Roblox Doğrulama Kodu", description=f"Merhaba **{interaction.user.name}**!\nRoblox hesabını (`{user_data['name']}`) doğrulamak için özel kodun aşağıdadır:\n\n🔑 **Doğrulama Kodun:** **`{code}`**\n\n**Adımlar:**\n1️⃣ Roblox profilindeki **Bio / Hakkımda** kısmına bu kodu yapıştır.\n2️⃣ Profilini kaydettikten sonra kanaldaki **`✅ Hesabı Doğrula`** butonuna bas!", color=discord.Color.dark_gray())
        embed_dm.set_footer(text="Güvenlik Departmanı - Özel Mesaj")

        try:
            await interaction.user.send(embed=embed_dm)
            await interaction.response.send_message("📩 **Doğrulama kodun DM kutuna gönderildi!** Lütfen DM'ni kontrol edip kodu ekledikten sonra butona bas.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ **DM kutunuz kapalı!** Kodu gönderebilmem için lütfen sunucu gizlilik ayarlarından DM mesajlarını açın.", ephemeral=True)

class KayitView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔗 Roblox Hesabını Bağla", style=discord.ButtonStyle.primary, custom_id="btn_kaydol")
    async def btn_kaydol_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(KayitModal())

    @discord.ui.button(label="✅ Hesabı Doğrula", style=discord.ButtonStyle.success, custom_id="btn_dogrula")
    async def btn_dogrula_callback(self, interaction: discord.Interaction, button: Button):
        user_id_str = str(interaction.user.id)
        if user_id_str not in pending_verifications:
            await interaction.response.send_message("❌ Önce **`🔗 Roblox Hesabını Bağla`** butonuna basmalısın!", ephemeral=True)
            return

        pending = pending_verifications[user_id_str]
        roblox_id = pending["roblox_id"]
        roblox_name = pending["roblox_name"]
        expected_code = pending["code"]

        res = requests.get(f"https://users.roblox.com/v1/users/{roblox_id}")
        if res.status_code != 200:
            await interaction.response.send_message("❌ Roblox profili çekilemedi.", ephemeral=True)
            return

        bio = res.json().get("description", "")

        if expected_code in bio:
            verified_users[user_id_str] = {"roblox_id": roblox_id, "roblox_name": roblox_name}
            save_users()
            del pending_verifications[user_id_str]

            guild = interaction.guild
            unverified_role = discord.utils.get(guild.roles, name="Kayıtsız")
            verified_role = discord.utils.get(guild.roles, name="Doğrulandi")

            if not verified_role:
                verified_role = await guild.create_role(name="Doğrulandi", color=discord.Color.green())

            try:
                if unverified_role and unverified_role in interaction.user.roles:
                    await interaction.user.remove_roles(unverified_role)
                if verified_role:
                    await interaction.user.add_roles(verified_role)
            except Exception as e:
                print(f"Rol hatası: {e}")

            try:
                await interaction.user.edit(nick=roblox_name)
                name_status = f" İsminiz **{roblox_name}** olarak güncellendi!"
            except Exception:
                name_status = " (İsminiz yetki seviyesi yüzünden değiştirilemedi ama rolleriniz verildi)."

            await interaction.response.send_message(f"✅ **Tebrikler!** Hesap başarıyla doğrulandı!{name_status}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Kod Roblox profil bio'nuzda bulunamadı!\nBeklenen Kod: **`{expected_code}`**", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(KayitView())
    bot.add_view(FormView())
    print(f'Bot {bot.user} olarak giriş yaptı ve göreve hazır!')

@bot.event
async def on_member_join(member):
    global WELCOME_CHANNEL_ID
    unverified_role = discord.utils.get(member.guild.roles, name="Kayıtsız")
    if unverified_role:
        try:
            await member.add_roles(unverified_role)
        except Exception:
            pass

    channel = None
    if WELCOME_CHANNEL_ID:
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    
    if channel is None:
        for ch in member.guild.text_channels:
            if "hoşgeldin" in ch.name.lower() or "welcome" in ch.name.lower() or "giriş" in ch.name.lower():
                channel = ch
                break
                
    if channel is None and member.guild.text_channels:
        channel = member.guild.text_channels[0]

    if channel:
        embed = discord.Embed(title="🎉 Yeni Üye Katıldı!", description=f"Aramıza hoş geldin {member.mention}!\n\n👤 **Kullanıcı Adı:** `{member.name}`\n🆔 **Discord ID:** `{member.id}`", color=discord.Color.dark_gray())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Güvenlik Departmanı Resmi Botu")
        await channel.send(content=f"👋 Hoş geldin {member.mention}!", embed=embed)

@bot.command()
async def form(ctx):
    embed = discord.Embed(title="📑 Güvenlik Departmanı - Form Paneli", description="Lütfen almak istediğiniz form butonuna tıklayın.", color=discord.Color.dark_gray())
    embed.set_footer(text="Güvenlik Departmanı Resmi Botu")
    await ctx.send(embed=embed, view=FormView())

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, amount: int = None):
    if amount is None or amount <= 0:
        await ctx.send("❌ Lütfen silinecek mesaj sayısını girin! Örnek: `!sil 10`", delete_after=5)
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    confirm_msg = await ctx.send(f"🗑️ **{len(deleted)-1}** adet mesaj silindi!")
    await confirm_msg.delete(delay=3)

@bot.command()
@commands.has_permissions(administrator=True)
async def kaydolkurulum(ctx, target_channel: discord.TextChannel = None):
    if target_channel is None:
        await ctx.send("❌ Lütfen bir kanal etiketleyin! Örnek: `!kaydolkurulum #kayıt-ol`")
        return
    guild = ctx.guild
    bilgi_msj = await ctx.send(f"⏳ **{target_channel.mention}** ayarlanıyor...")
    unverified_role = discord.utils.get(guild.roles, name="Kayıtsız")
    if not unverified_role:
        unverified_role = await guild.create_role(name="Kayıtsız", color=discord.Color.red())
    verified_role = discord.utils.get(guild.roles, name="Doğrulandi")
    if not verified_role:
        verified_role = await guild.create_role(name="Doğrulandi", color=discord.Color.green())

    for m in guild.members:
        if not m.bot and verified_role not in m.roles:
            try:
                await m.add_roles(unverified_role)
            except Exception:
                pass

    for channel in guild.channels:
        if channel.id == target_channel.id:
            await channel.set_permissions(guild.default_role, read_messages=True, send_messages=False)
            await channel.set_permissions(unverified_role, read_messages=True, send_messages=False)
            await channel.set_permissions(verified_role, read_messages=True, send_messages=False)
        else:
            await channel.set_permissions(guild.default_role, read_messages=False)
            await channel.set_permissions(unverified_role, read_messages=False)
            await channel.set_permissions(verified_role, read_messages=True)

    try:
        await target_channel.purge(limit=1000)
    except Exception as e:
        print(f"Purge hatası: {e}")

    embed = discord.Embed(title="🛡️ Güvenlik Departmanı - Roblox Doğrulama Paneli", description="Sunucuya erişim için hesabınızı bağlayın:\n\n1️⃣ **`🔗 Roblox Hesabını Bağla`** butonuna basın.\n2️⃣ DM'den gelen kodu profil bio'nuza ekleyin.\n3️⃣ **`✅ Hesabı Doğrula`** butonuna basın.", color=discord.Color.dark_gray())
    embed.set_footer(text="Güvenlik Departmanı Botu")
    await target_channel.send(embed=embed, view=KayitView())
    await bilgi_msj.edit(content=f"✅ **{target_channel.mention}** kuruldu!")

@bot.command()
@commands.has_permissions(administrator=True)
async def kurulum(ctx, target_channel: discord.TextChannel = None):
    global WELCOME_CHANNEL_ID
    if target_channel is None:
        await ctx.send("❌ Lütfen bir kanal etiketleyin! Örnek: `!kurulum #hoşgeldin`")
        return
    WELCOME_CHANNEL_ID = target_channel.id
    bilgi_msj = await ctx.send(f"⏳ **{target_channel.mention}** ayarlanıyor...")
    try:
        await target_channel.purge(limit=1000)
    except Exception as e:
        print(f"Hata: {e}")
    await target_channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🎉 Hoşgeldin!", description="Sunucumuza hoş geldiniz!", color=discord.Color.dark_gray())
    await target_channel.send(embed=embed)
    await bilgi_msj.edit(content=f"✅ **{target_channel.mention}** kuruldu!")

@bot.command()
async def liste(ctx):
    await ctx.send("🔄 Rütbeler taranıyor...")
    try:
        roles_url = f"https://groups.roblox.com/v1/groups/{ROBLOX_GROUP_ID}/roles"
        roles_res = requests.get(roles_url)
        if roles_res.status_code != 200:
            await ctx.send("❌ Roblox rütbe bilgileri çekilemedi.")
            return
        roles_data = roles_res.json().get("roles", [])
        sorted_roles = sorted(roles_data, key=lambda r: r.get("rank", 0), reverse=True)
        list_text = ""
        user_count = 0
        for role in sorted_roles:
            if role.get("rank") == 0:
                continue
            users_url = f"https://groups.roblox.com/v1/groups/{ROBLOX_GROUP_ID}/roles/{role.get('id')}/users?sortOrder=Desc&limit=10"
            users_res = requests.get(users_url)
            if users_res.status_code == 200:
                for u in users_res.json().get("data", []):
                    list_text += f"🎖️ **{role.get('name')}** | 👤 **{u.get('username')}** (`{u.get('userId')}`)\n"
                    user_count += 1
                    if user_count >= 25:
                        break
            if user_count >= 25:
                break
        embed = discord.Embed(title="🛡️ Rütbe Listesi", description=list_text if list_text else "Üye bulunamadı.", color=discord.Color.dark_gray())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Hata: {e}")

@bot.command()
async def rütbebilgi(ctx):
    embed = discord.Embed(title="📘 Rehber", description="Bot kullanım rehberi.", color=discord.Color.dark_gray())
    await ctx.send(embed=embed)

@bot.command()
async def yardım(ctx):
    embed = discord.Embed(title="📖 Yardım Menüsü", description="Tüm komutlar.", color=discord.Color.dark_gray())
    await ctx.send(embed=embed)

bot.run(BOT_TOKEN)
