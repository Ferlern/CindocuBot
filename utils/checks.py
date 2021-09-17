def confirm_check(ctx):
    original_author = ctx.message.author

    def check(interaction):
        return interaction.author == original_author

    return check
