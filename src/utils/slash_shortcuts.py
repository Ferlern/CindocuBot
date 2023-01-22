import disnake


only_admin = {
    'dm_permission': False,
    'default_member_permissions': disnake.Permissions(administrator=True)
}
