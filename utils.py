# utils.py
def styled_plot(fig, height=400):
    fig.update_layout(
        height=height,
        plot_bgcolor="#E4E1DC",
        paper_bgcolor="#E4E1DC",
        font=dict(color="#2B2B2B", size=12),
        margin=dict(l=20, r=20, t=40, b=40)
    )
    return fig
