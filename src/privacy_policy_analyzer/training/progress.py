import time
from logging import info

from transformers import TrainerCallback, TrainerState


class SimpleProgressBarCallback(TrainerCallback):
    """
    Simple progress bar that logs updates at each logging step.
    """

    def __init__(self, name: str):
        self.start_time = None
        self.name = name
        self.last_epoch = 0

    def on_train_begin(self, args, state, control, **kwargs):
        self.start_time = time.time()
        self.total_epochs = args.num_train_epochs
        print(f"Training for {self.total_epochs} epochs")

    def on_step_end(self, args, state, control, **kwargs):
        print(
            f"\rEpoch [{state.epoch:.2f}/{self.total_epochs:.2f}] - Step [{state.global_step}/{state.max_steps}] - Progress: {state.global_step / state.max_steps * 100:.2f}%",
            end="",
            flush=True,
        )

    def on_log(self, args, state, control, logs=None, **kwargs):
        pass

    def on_evaluate(self, args, state: TrainerState, control, **kwargs):
        hist = state.log_history
        if len(hist) > 0 and state.epoch != self.last_epoch:
            latest = hist[-1]

            f1_macro = latest.get("eval_f1_macro", None)
            f1_micro = latest.get("eval_f1_micro", None)
            eval_loss = latest.get("eval_loss", None)

            assert self.start_time is not None
            elapsed_time = (time.time() - self.start_time) / 60
            print()
            info(
                f"Epoch: {state.epoch} | Eval Loss: {eval_loss:.3f} | F1 Macro: {f1_macro:.3f} | F1 Micro: {f1_micro:.3f} | Elapsed Time: {elapsed_time:.2f}"
            )

            self.last_epoch = state.epoch

    def on_train_end(self, args, state, control, **kwargs):
        assert self.start_time is not None
        duration = time.time() - self.start_time
        info(f"==[*]==  Training completed! {duration} ==[*]==")
