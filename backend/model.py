"""Simple PyTorch model utilities.
Contains a minimal model and helpers to flatten/unflatten weights for easy transfer.
"""
import torch
import torch.nn as nn


class SimpleNet(nn.Module):
    def __init__(self, input_size=64, hidden=32, out=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out)
        )

    def forward(self, x):
        return self.net(x)


def get_flat_weights(model: nn.Module):
    """Return model weights as a single flat Python list of floats."""
    flat = []
    for p in model.state_dict().values():
        arr = p.detach().cpu().numpy().ravel().tolist()
        flat.extend(arr)
    return flat


def set_flat_weights(model: nn.Module, flat_list):
    """Set model weights from a flat list (assumes matching architecture)."""
    state = model.state_dict()
    pointer = 0
    new_state = {}
    for k, v in state.items():
        numel = v.numel()
        slice_vals = flat_list[pointer : pointer + numel]
        tensor = torch.tensor(slice_vals, dtype=v.dtype).view(v.size())
        new_state[k] = tensor
        pointer += numel
    model.load_state_dict(new_state)
