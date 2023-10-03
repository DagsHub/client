import random
from multiprocessing import Process
from typing import TYPE_CHECKING, Union

from dagshub.common.util import lazy_load
from dagshub.data_engine.client.loaders.base import DagsHubDataset

np = lazy_load("numpy")
tf = lazy_load("tensorflow")

if TYPE_CHECKING:
    import tensorflow as tf


class TensorFlowDataset(DagsHubDataset):
    def __init__(self, *args, **kwargs):
        self.tensorlib = Tensorizers
        super().__init__(*args, **kwargs)
        self.signature = tuple(tf.TensorSpec.from_tensor(tensor) for tensor in next(self.generator()))

    def generator(self):
        for idx in range(len(self)):
            yield tuple(self[idx])


class TensorFlowDataLoader(tf.keras.utils.Sequence):
    def __init__(
        self,
        dataset,
        batch_size=1,
        shuffle=True,
        seed=None,
        post_hook=lambda x: x,
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.post_hook = post_hook

        if seed:
            random.seed(seed)
            np.random.seed(seed)

        self.indices = {}
        self.on_epoch_end()

        self.dataset.builder.order = self.indices
        if self.dataset.builder.strategy == "background":
            Process(target=self.dataset.builder.pull).start()

    def __len__(self) -> int:
        return self.dataset.__len__() // self.batch_size

    def __getitem__(self, index: int) -> tf.Tensor:
        samples = [
            self.dataset.__getitem__(index)
            for index in self.indices[index * self.batch_size : (index + 1) * self.batch_size]
        ]
        batch = [[] for _ in range(len(samples[0]))]  # [[]] * len(samples[0]) creates lists shallowly
        for sample in samples:
            for idx, tensor in enumerate(sample):
                batch[idx].append(tensor)

        return tuple(self.post_hook([tf.stack(column) for column in batch]))

    def on_epoch_end(self) -> None:
        self.indices = np.arange(self.dataset.__len__())
        if self.shuffle:
            np.random.shuffle(self.indices)


class Tensorizers:
    @staticmethod
    def image(filepath: str) -> tf.Tensor:
        return tf.convert_to_tensor(tf.keras.utils.load_img(filepath))

    @staticmethod
    def audio(filepath: str) -> tf.Tensor:
        return tf.audio.decode_wav(
            tf.io.read_file(str(filepath)),
            desired_channels=-1,
            desired_samples=-1,
            name=None,
        )

    @staticmethod
    def video(filepath: str) -> tf.Tensor:
        raise NotImplementedError("Coming Soon!")

    @staticmethod
    def numeric(num: Union[float, int]) -> tf.Tensor:
        return tf.convert_to_tensor(num)
